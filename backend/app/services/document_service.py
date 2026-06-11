"""文档服务 — 文档上传、删除、状态管理、异步处理触发

DocumentService 封装了所有与文档相关的业务逻辑：
- 上传文档时校验文件类型、保存文件、触发异步处理
- 支持文档查询、列表（按数据集）、删除
- 文档处理状态查询
- 文档切片列表查询
- 用户隔离：用户只能操作自己的文档

依赖:
    - DatabaseManager（异步数据库会话）
    - FileStorageBackend（文件存储）
    - TaskQueueBackend（异步任务队列）
    - DocumentPipeline（文档处理管道，用于触发处理）
"""

import os
from typing import List, Optional, Tuple

from sqlalchemy import func, select

from app.core.database import DatabaseManager
from app.core.exceptions import RagError
from app.core.storage import FileStorageBackend
from app.core.task_queue import TaskQueueBackend
from app.models.chunk import Chunk
from app.models.document import Document
from app.rag.pipeline import DocumentPipeline
from app.schemas.chunk import ChunkResponse
from app.schemas.document import DocumentResponse, DocumentStatusResponse


# ════════════════════════════════════════════════════════════
# 业务异常
# ════════════════════════════════════════════════════════════


class DocumentServiceError(RagError):
    """文档服务相关错误的基类"""

    def __init__(
        self,
        code: str = "document_service_error",
        message: str = "文档服务错误",
        detail: object = None,
    ) -> None:
        super().__init__(code=code, message=message, detail=detail)


class DocumentNotFound(DocumentServiceError):
    """文档不存在"""

    def __init__(self, document_id: str) -> None:
        super().__init__(
            code="document_not_found",
            message="文档不存在",
            detail={"document_id": document_id},
        )


class DocumentPermissionDenied(DocumentServiceError):
    """无权访问该文档"""

    def __init__(self, document_id: str) -> None:
        super().__init__(
            code="document_permission_denied",
            message="无权访问该文档",
            detail={"document_id": document_id},
        )


class UnsupportedFileType(DocumentServiceError):
    """不支持的文件格式"""

    def __init__(self, file_type: str) -> None:
        super().__init__(
            code="unsupported_file_type",
            message=f"不支持的文件格式: {file_type}",
            detail={"file_type": file_type},
        )


# ════════════════════════════════════════════════════════════
# 文档服务
# ════════════════════════════════════════════════════════════


class DocumentService:
    """文档服务

    提供文档的完整生命周期管理：
    - 上传文档时校验文件类型、保存文件、创建记录、触发异步处理
    - 查询文档详情和状态
    - 按数据集列出文档（分页）
    - 删除文档（清理文件 + 数据库记录）
    - 查询文档切片列表

    所有公开方法均为 async，且所有操作均校验用户身份。

    用法::

        service = DocumentService(db_manager, storage, task_queue, pipeline)
        doc = await service.upload_document(user_id="...", dataset_id="...", ...)
        status = await service.get_document_status(doc_id="...", user_id="...")
    """

    ALLOWED_EXTENSIONS = frozenset({
        ".txt", ".md", ".text", ".markdown",
        ".pdf", ".PDF",
        ".docx", ".DOCX",
        ".pptx", ".PPTX",
        ".xlsx", ".XLSX",
        ".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG",
    })

    def __init__(
        self,
        db: DatabaseManager,
        storage: FileStorageBackend,
        task_queue: TaskQueueBackend,
        pipeline: DocumentPipeline,
    ) -> None:
        self._db = db
        self._storage = storage
        self._task_queue = task_queue
        self._pipeline = pipeline

    # ── 上传文档 ──────────────────────────────────────────────

    async def upload_document(
        self,
        user_id: str,
        dataset_id: str,
        filename: str,
        content: bytes,
    ) -> DocumentResponse:
        """上传文档并触发异步处理

        流程:
            1. 检查文件扩展名是否在允许列表中
            2. 保存文件到存储后端
            3. 创建 Document 数据库记录（状态为 pending）
            4. 入队异步处理任务
            5. 返回刚创建的文档信息

        参数:
            user_id:    所属用户 ID
            dataset_id: 所属数据集 ID
            filename:   原始文件名（含扩展名）
            content:    文件二进制内容

        返回:
            DocumentResponse — 包含文档 ID、状态等完整信息

        异常:
            UnsupportedFileType — 文件格式不被支持
        """
        # 检查文件类型
        ext = os.path.splitext(filename)[1]
        if ext not in self.ALLOWED_EXTENSIONS:
            raise UnsupportedFileType(ext)

        # 保存文件
        import uuid

        storage_path = f"users/{user_id}/{uuid.uuid4()}{ext}"
        full_path = await self._storage.save(storage_path, content)

        # 创建 Document 记录
        async with self._db.get_session() as session:
            doc = Document(
                filename=filename,
                file_type=ext.lstrip(".").lower(),
                file_size=len(content),
                file_path=full_path,
                status="pending",
                dataset_id=dataset_id,
                user_id=user_id,
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            doc_id = doc.id

        # 异步触发文档处理
        self._task_queue.enqueue("process_document", doc_id)

        return await self.get_document(doc_id, user_id)

    # ── 查询单个文档 ──────────────────────────────────────────

    async def get_document(self, doc_id: str, user_id: str) -> DocumentResponse:
        """根据 ID 获取文档信息（含用户隔离检查）

        异常:
            DocumentNotFound — 文档不存在
        """
        async with self._db.get_session() as session:
            result = await session.execute(
                select(Document).where(
                    Document.id == doc_id,
                    Document.user_id == user_id,
                )
            )
            doc = result.scalar_one_or_none()

        if doc is None:
            raise DocumentNotFound(doc_id)

        return self._to_response(doc)

    # ── 文档列表（按数据集分页） ──────────────────────────────

    async def list_documents(
        self,
        dataset_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取指定数据集下的文档列表（分页），按创建时间倒序

        参数:
            dataset_id: 数据集 ID
            user_id:    用户 ID（过滤，确保只返回该用户的）
            page:       页码（从 1 开始）
            page_size:  每页条数

        返回:
            {"items": [DocumentResponse, ...], "total": int, "page": int, "page_size": int}
        """
        async with self._db.get_session() as session:
            # 总数
            count_result = await session.execute(
                select(func.count(Document.id)).where(
                    Document.dataset_id == dataset_id,
                    Document.user_id == user_id,
                )
            )
            total: int = count_result.scalar() or 0

            # 分页查询
            offset = (page - 1) * page_size
            result = await session.execute(
                select(Document)
                .where(
                    Document.dataset_id == dataset_id,
                    Document.user_id == user_id,
                )
                .order_by(Document.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            docs = result.scalars().all()

        items = [self._to_response(d) for d in docs]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    # ── 删除文档 ──────────────────────────────────────────────

    async def delete_document(self, doc_id: str, user_id: str) -> None:
        """删除文档（清理文件 + 数据库记录）

        流程:
            1. 查询文档并校验归属
            2. 从存储后端删除文件
            3. 删除数据库记录（ORM cascade 会清理关联的切片）
            4. 向量库清理由异步任务处理

        异常:
            DocumentNotFound — 文档不存在
        """
        async with self._db.get_session() as session:
            result = await session.execute(
                select(Document).where(
                    Document.id == doc_id,
                    Document.user_id == user_id,
                )
            )
            doc = result.scalar_one_or_none()

            if doc is None:
                raise DocumentNotFound(doc_id)

            # 记录文件路径（提交后 session 不可用）
            file_path = doc.file_path

            # 删除数据库记录（ORM cascade 删除切片）
            await session.delete(doc)
            await session.commit()

        # 删除存储文件（在 session 外执行）
        await self._storage.delete(file_path)

        # 注：向量库清理由异步任务处理

    # ── 文档处理状态 ──────────────────────────────────────────

    async def get_document_status(
        self,
        doc_id: str,
        user_id: str,
    ) -> DocumentStatusResponse:
        """获取文档处理状态及进度

        状态 → 进度映射:
            - pending   → 0.0（等待处理）
            - parsing   → 0.2（解析中）
            - splitting → 0.4（切片中）
            - indexing  → 0.7（索引中）
            - completed → 1.0（已完成）
            - failed    → 0.0（处理失败）

        异常:
            DocumentNotFound — 文档不存在
        """
        async with self._db.get_session() as session:
            result = await session.execute(
                select(Document).where(
                    Document.id == doc_id,
                    Document.user_id == user_id,
                )
            )
            doc = result.scalar_one_or_none()

        if doc is None:
            raise DocumentNotFound(doc_id)

        progress_map = {
            "pending": 0.0,
            "parsing": 0.2,
            "splitting": 0.4,
            "indexing": 0.7,
            "completed": 1.0,
            "failed": 0.0,
        }
        return DocumentStatusResponse(
            id=doc.id,
            status=doc.status,
            progress=progress_map.get(doc.status, 0.0),
            error_message=doc.error_message,
        )

    # ── 文档切片列表 ──────────────────────────────────────────

    async def list_chunks(
        self,
        doc_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """获取指定文档的切片列表（分页），按切片序号升序

        参数:
            doc_id:    文档 ID
            user_id:   用户 ID（用于验证文档归属）
            page:      页码（从 1 开始）
            page_size: 每页条数

        返回:
            {"items": [ChunkResponse, ...], "total": int, "page": int, "page_size": int}

        异常:
            DocumentNotFound — 文档不存在
        """
        async with self._db.get_session() as session:
            # 验证文档属于该用户
            doc_result = await session.execute(
                select(Document).where(
                    Document.id == doc_id,
                    Document.user_id == user_id,
                )
            )
            if doc_result.scalar_one_or_none() is None:
                raise DocumentNotFound(doc_id)

            # 总数
            count_result = await session.execute(
                select(func.count(Chunk.id)).where(Chunk.document_id == doc_id)
            )
            total: int = count_result.scalar() or 0

            # 分页查询
            offset = (page - 1) * page_size
            result = await session.execute(
                select(Chunk)
                .where(Chunk.document_id == doc_id)
                .order_by(Chunk.chunk_index)
                .offset(offset)
                .limit(page_size)
            )
            chunks = result.scalars().all()

        items = [
            ChunkResponse(
                id=c.id,
                document_id=c.document_id,
                content=c.content,
                chunk_index=c.chunk_index,
                metadata=c.meta_data,
            )
            for c in chunks
        ]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    # ── 内部辅助 ──────────────────────────────────────────────

    @staticmethod
    def _to_response(doc: Document) -> DocumentResponse:
        """将 Document ORM 对象转换为 DocumentResponse Pydantic 模式"""
        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status,
            error_message=doc.error_message,
            dataset_id=doc.dataset_id,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
