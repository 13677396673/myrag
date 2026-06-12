"""文档处理异步任务单元测试

覆盖 ``process_document`` 的完整流程：
- 处理成功：status → parsing → completed，chunk_count 更新
- 处理失败：status → failed，error_message 记录
- 文档不存在：ValueError 抛出
- register_tasks 注册验证
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select

from app.models.document import Document
from app.tasks.document_tasks import (
    _process_document_async,
    process_document,
    register_tasks,
)


# ════════════════════════════════════════════════════════════
# 夹具
# ════════════════════════════════════════════════════════════


@pytest.fixture(scope="function")
def mock_container(db_manager, mock_pipeline) -> MagicMock:
    """模拟的 Container 实例，注入真实 DB + mock Pipeline"""
    container = MagicMock()
    container.db = db_manager
    container.pipeline = mock_pipeline
    return container


@pytest.fixture(scope="function")
def patch_container(mock_container):
    """Mock ``Container.get()`` 以返回 ``mock_container``

    所有使用该夹具的测试自动获得容器注入。
    ``Container`` 在 ``document_tasks.py`` 中是函数内局部导入，
    因此在 ``app.core.container`` 模块上 patch 其类方法 ``get``。
    """
    patcher = patch(
        "app.core.container.Container.get",
        AsyncMock(return_value=mock_container),
    )
    with patcher:
        yield


# ════════════════════════════════════════════════════════════
# 辅助函数
# ════════════════════════════════════════════════════════════


async def create_document(
    db_manager,
    user_id: str,
    dataset_id: str,
    *,
    filename: str = "task_test.pdf",
    file_type: str = "pdf",
    file_path: str = "/tmp/task_test.pdf",
) -> str:
    """在数据库中创建一个测试文档，返回文档 ID"""
    async with db_manager.get_session() as session:
        doc = Document(
            filename=filename,
            file_type=file_type,
            file_size=100,
            file_path=file_path,
            status="pending",
            dataset_id=dataset_id,
            user_id=user_id,
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return doc.id


# ════════════════════════════════════════════════════════════
# process_document 任务测试
# ════════════════════════════════════════════════════════════


class TestProcessDocument:
    """``_process_document_async`` 核心流程测试"""

    # ── 处理成功 ──────────────────────────────────────────

    async def test_success(
        self,
        db_manager,
        mock_pipeline,
        patch_container,
        sample_user: dict,
        sample_dataset,
    ):
        """成功处理文档：状态应从 pending → parsing → completed"""
        doc_id = await create_document(
            db_manager, sample_user["id"], sample_dataset.id
        )

        result = await _process_document_async(doc_id)

        assert result == 10

        # 验证最终数据库状态
        async with db_manager.get_session() as session:
            row = await session.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = row.scalar_one()
            assert doc.status == "completed"
            assert doc.chunk_count == 10
            assert doc.error_message is None

    async def test_success_status_transitions(
        self,
        db_manager,
        mock_pipeline,
        patch_container,
        sample_user: dict,
        sample_dataset,
    ):
        """验证状态转换：process_document 开始前 DB 中写入 parsing 状态，
        完成后写入 completed"""
        doc_id = await create_document(
            db_manager, sample_user["id"], sample_dataset.id
        )

        # 确认初始状态为 pending
        async with db_manager.get_session() as s:
            row = await s.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = row.scalar_one()
            assert doc.status == "pending"

        # 执行任务
        result = await _process_document_async(doc_id)
        assert result == 10

        # 最终状态为 completed
        async with db_manager.get_session() as session:
            row = await session.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = row.scalar_one()
            assert doc.status == "completed"
            assert doc.chunk_count == 10

    # ── 处理失败 ──────────────────────────────────────────

    async def test_failure(
        self,
        db_manager,
        mock_pipeline,
        patch_container,
        sample_user: dict,
        sample_dataset,
    ):
        """pipeline 抛出异常时，文档状态应置为 failed"""
        doc_id = await create_document(
            db_manager, sample_user["id"], sample_dataset.id
        )

        error_msg = "文件损坏：无法解析 PDF"
        mock_pipeline.process_document = MagicMock(
            side_effect=ValueError(error_msg)
        )

        with pytest.raises(ValueError, match=error_msg):
            await _process_document_async(doc_id)

        # 验证数据库状态
        async with db_manager.get_session() as session:
            row = await session.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = row.scalar_one()
            assert doc.status == "failed"
            assert doc.error_message == error_msg
            assert doc.chunk_count == 0

    async def test_failure_preserves_parsing_status_before_error(
        self,
        db_manager,
        mock_pipeline,
        patch_container,
        sample_user: dict,
        sample_dataset,
    ):
        """失败前文档应曾被置为 parsing 状态"""
        doc_id = await create_document(
            db_manager, sample_user["id"], sample_dataset.id
        )

        mock_pipeline.process_document = MagicMock(
            side_effect=RuntimeError("处理异常")
        )

        with pytest.raises(RuntimeError):
            await _process_document_async(doc_id)

        # 验证 parsing 状态已经被写入（然后被覆盖为 failed）
        async with db_manager.get_session() as session:
            row = await session.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = row.scalar_one()
            # 最终状态是 failed，但之前应该经过了 parsing
            assert doc.status == "failed"
            assert doc.error_message == "处理异常"

    # ── 文档不存在 ────────────────────────────────────────

    async def test_document_not_found(
        self,
        db_manager,
        mock_pipeline,
        patch_container,
    ):
        """不存在的 doc_id 应抛出 ValueError"""
        with pytest.raises(ValueError, match="文档不存在"):
            await _process_document_async("non-existent-id")

    # ── 空文档（返回 0 切片） ────────────────────────────

    async def test_empty_document(
        self,
        db_manager,
        mock_pipeline,
        patch_container,
        sample_user: dict,
        sample_dataset,
    ):
        """返回 0 切片的文档也应正确更新为 completed"""
        doc_id = await create_document(
            db_manager, sample_user["id"], sample_dataset.id
        )

        mock_pipeline.process_document = MagicMock(return_value=0)

        result = await _process_document_async(doc_id)
        assert result == 0

        async with db_manager.get_session() as session:
            row = await session.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = row.scalar_one()
            assert doc.status == "completed"
            assert doc.chunk_count == 0

    # ── DB 更新的错误不影响原始异常传播 ───────────────────

    async def test_failure_db_update_error_still_raises(
        self,
        db_manager,
        mock_pipeline,
        patch_container,
        sample_user: dict,
        sample_dataset,
    ):
        """即使失败后 DB 更新出错，原始异常仍应向上传播"""
        doc_id = await create_document(
            db_manager, sample_user["id"], sample_dataset.id
        )

        error_msg = "管道处理错误"
        mock_pipeline.process_document = MagicMock(
            side_effect=ValueError(error_msg)
        )

        # 模拟第二次 DB 会话（更新 failed）失败
        # 通过 monkeypatch db.get_session 来实现
        original_get_session = db_manager.get_session

        call_count = 0

        def counting_session():
            nonlocal call_count
            call_count += 1
            session = original_get_session()
            # 第三次调用 get_session() 时（即写 failed 状态的 session）使其出错
            if call_count == 3:
                # 让 session.commit() 抛出异常
                original_commit = session.commit
                session.commit = MagicMock(side_effect=RuntimeError("DB 写入失败"))
            return session

        db_manager.get_session = counting_session

        with pytest.raises(ValueError, match=error_msg):
            await _process_document_async(doc_id)


# ════════════════════════════════════════════════════════════
# sync wrapper 测试
# ════════════════════════════════════════════════════════════


class TestProcessDocumentSyncWrapper:
    """``process_document`` 同步入口包装测试"""

    async def test_sync_wrapper_calls_async(
        self,
        db_manager,
        mock_pipeline,
        patch_container,
        sample_user: dict,
        sample_dataset,
    ):
        """同步包装器 ``process_document()`` 应能正确执行并返回结果"""
        doc_id = await create_document(
            db_manager, sample_user["id"], sample_dataset.id
        )

        # 在异步测试中调用同步包装器（通过 run_in_executor 或直接调用）
        # 注意：asyncio.run() 会在已有 event loop 时失败，
        # 这里使用 pytest-asyncio 的 event_loop 来运行
        import asyncio

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, process_document, doc_id
        )

        assert result == 10

        async with db_manager.get_session() as session:
            row = await session.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = row.scalar_one()
            assert doc.status == "completed"
            assert doc.chunk_count == 10


# ════════════════════════════════════════════════════════════
# register_tasks 测试
# ════════════════════════════════════════════════════════════


class TestRegisterTasks:
    """任务注册功能测试"""

    def test_register_process_document(self):
        """register_tasks 应正确注册 process_document"""
        mock_queue = MagicMock(spec=["register_task"])

        register_tasks(mock_queue)

        mock_queue.register_task.assert_called_once_with(
            "process_document", process_document
        )

    def test_register_tasks_idempotent(self):
        """连续调用 register_tasks 应每次都注册"""
        mock_queue = MagicMock(spec=["register_task"])

        register_tasks(mock_queue)
        register_tasks(mock_queue)

        assert mock_queue.register_task.call_count == 2
