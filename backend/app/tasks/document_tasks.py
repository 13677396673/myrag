"""文档处理异步任务定义

本模块包含所有与文档处理相关的异步任务函数，供 ``TaskQueueBackend``
注册和调度。每个任务以同步函数形式暴露（适配 Huey 等同步任务队列），
内部通过 ``asyncio.run()`` 驱动异步操作。

使用流程::

    from app.tasks.document_tasks import register_tasks
    from app.core.task_queue import HueyTaskQueue

    queue = HueyTaskQueue()
    register_tasks(queue)          # 注册所有任务
    queue.enqueue("process_document", doc_id="doc-001")  # 入队
"""

import asyncio
import logging

from sqlalchemy import select

from app.models.document import Document

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# process_document
# ════════════════════════════════════════════════════════════


def process_document(doc_id: str) -> int:
    """处理文档的主任务（同步入口，供 Huey 等同步任务队列调用）

    在独立消费者进程中运行时，通过 ``asyncio.run()`` 驱动内部的
    异步操作（数据库读写）。返回处理生成的切片数量。

    在 ``immediate=True`` 模式下，如果从异步上下文调用（如 uvicorn），
    ``asyncio.run()`` 不能被直接使用，会在独立线程中创建新的事件循环执行。

    流程:
        1. 从 DB 获取 Document 记录，更新 status → "parsing"
        2. 调用 pipeline.process_document() 完成 解析→切片→Embedding→入库
        3. 更新 DB：status → "completed"、chunk_count
        4. 任何异常 → status → "failed" + 记录 error_message

    参数:
        doc_id: 文档 ID

    返回:
        生成的切片数量

    异常:
        ValueError: 文档不存在时抛出
    """
    try:
        asyncio.get_running_loop()
        # 已有运行中的事件循环（如 Huey immediate 模式从 async 上下文调用）
        # 在独立线程中创建新事件循环执行
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, _process_document_async(doc_id))
            return future.result()
    except RuntimeError:
        # 没有运行中的事件循环——正常 asyncio.run 模式
        return asyncio.run(_process_document_async(doc_id))


async def _process_document_async(doc_id: str) -> int:
    """``process_document`` 的异步实现

    拆分为独立函数以便单元测试直接测试异步逻辑，无需通过
    ``asyncio.run()`` 包装。
    """
    from app.core.container import Container

    container = await Container.get()
    db = container.db
    pipeline = container.pipeline

    # ── Step 1: 查询文档并更新状态为 "parsing" ──────────────
    async with db.get_session() as session:
        result = await session.execute(
            select(Document).where(Document.id == doc_id)
        )
        doc = result.scalar_one_or_none()

        if doc is None:
            raise ValueError(f"文档不存在: {doc_id}")

        # 保存 session 关闭后仍需使用的字段
        file_path = doc.file_path
        user_id = doc.user_id
        dataset_id = doc.dataset_id
        original_filename = doc.filename

        doc.status = "parsing"
        await session.commit()

    # ── Step 2: 执行文档处理管道（同步操作） ─────────────────
    try:
        chunk_count = pipeline.process_document(
            file_path=file_path,
            document_id=doc_id,
            user_id=user_id,
            dataset_id=dataset_id,
            filename=original_filename,
        )

        # ── Step 2.5: 保存切片到 SQL Chunk 表 ──────────────
        if chunk_count > 0 and pipeline.last_chunks:
            from app.models.chunk import Chunk as ChunkModel
            async with db.get_session() as session:
                for c in pipeline.last_chunks:
                    chunk_sql_id = f"{doc_id}_{c.chunk_index}"  # 与 ChromaDB chunk_id 一致
                    session.add(ChunkModel(
                        id=chunk_sql_id,
                        document_id=doc_id,
                        content=c.content,
                        chunk_index=c.chunk_index,
                        meta_data=dict(c.metadata),
                    ))
                await session.commit()

        # ── Step 3: 更新状态为 "completed" ──────────────────
        async with db.get_session() as session:
            result = await session.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = result.scalar_one()
            doc.status = "completed"
            doc.chunk_count = chunk_count
            await session.commit()

        logger.info("文档 %s 处理完成，共 %d 个切片", doc_id, chunk_count)
        return chunk_count

    except Exception as exc:
        # ── Step 4: 异常 → 更新为 "failed" ─────────────────
        logger.error("文档 %s 处理失败: %s", doc_id, exc)
        try:
            async with db.get_session() as session:
                result = await session.execute(
                    select(Document).where(Document.id == doc_id)
                )
                doc = result.scalar_one()
                doc.status = "failed"
                doc.error_message = str(exc)
                await session.commit()
        except Exception as db_exc:
            logger.error(
                "文档 %s 处理失败后无法更新 DB 状态: %s", doc_id, db_exc
            )
        raise


# ════════════════════════════════════════════════════════════
# 注册辅助
# ════════════════════════════════════════════════════════════


def register_tasks(task_queue) -> None:
    """注册所有文档处理任务到 ``TaskQueueBackend``

    应在应用启动时调用，通常与 ``Container`` 初始化一起完成。

    用法::

        from app.core.task_queue import HueyTaskQueue
        from app.tasks.document_tasks import register_tasks

        queue = HueyTaskQueue()
        register_tasks(queue)

    参数:
        task_queue: 实现了 ``TaskQueueBackend`` 接口的任务队列实例
    """
    task_queue.register_task("process_document", process_document)
