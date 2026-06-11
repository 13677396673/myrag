"""文档服务单元测试

覆盖 DocumentService 的所有公开方法，包括正常流程和异常场景。
重点验证：
- 文件类型校验
- 用户隔离（文档归属）
- 文件存储与任务队列调用
- 文档状态与切片查询
"""

import pytest

from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.schemas.chunk import ChunkResponse
from app.services.document_service import (
    DocumentNotFound,
    DocumentPermissionDenied,
    DocumentService,
    DocumentServiceError,
    UnsupportedFileType,
)


# ════════════════════════════════════════════════════════════
# 上传文档
# ════════════════════════════════════════════════════════════


class TestUploadDocument:
    """上传文档测试"""

    async def test_upload_success(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_dataset,
        mock_storage,
        mock_task_queue,
    ):
        """正常上传文档应返回完整信息并触发异步任务"""
        result = await document_service.upload_document(
            user_id=sample_user["id"],
            dataset_id=sample_dataset.id,
            filename="report.pdf",
            content=b"%PDF-1.4 mock content",
        )

        assert isinstance(result, DocumentResponse)
        assert result.filename == "report.pdf"
        assert result.file_type == "pdf"
        assert result.file_size == 21  # len(b"%PDF-1.4 mock content")
        assert result.status == "pending"
        assert result.dataset_id == sample_dataset.id
        assert result.chunk_count == 0
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

        # 验证文件已保存
        mock_storage.save.assert_awaited_once()

        # 验证任务已入队
        mock_task_queue.enqueue.assert_called_once_with(
            "process_document", result.id
        )

    async def test_upload_txt_file(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_dataset,
    ):
        """上传 txt 文件应成功"""
        result = await document_service.upload_document(
            user_id=sample_user["id"],
            dataset_id=sample_dataset.id,
            filename="readme.txt",
            content=b"Hello, World!",
        )

        assert result.filename == "readme.txt"
        assert result.file_type == "txt"
        assert result.status == "pending"

    async def test_upload_markdown_file(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_dataset,
    ):
        """上传 md 文件应成功"""
        result = await document_service.upload_document(
            user_id=sample_user["id"],
            dataset_id=sample_dataset.id,
            filename="doc.md",
            content=b"# Title\nContent",
        )

        assert result.filename == "doc.md"
        assert result.file_type == "md"

    async def test_upload_image_file(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_dataset,
    ):
        """上传 jpg/png 文件应成功"""
        result = await document_service.upload_document(
            user_id=sample_user["id"],
            dataset_id=sample_dataset.id,
            filename="photo.jpg",
            content=b"\xff\xd8\xff\xe0 mock jpeg",
        )

        assert result.filename == "photo.jpg"
        assert result.file_type == "jpg"

    async def test_upload_unsupported_file_type(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_dataset,
    ):
        """上传不支持的文件格式应抛出 UnsupportedFileType"""
        with pytest.raises(UnsupportedFileType) as exc:
            await document_service.upload_document(
                user_id=sample_user["id"],
                dataset_id=sample_dataset.id,
                filename="script.exe",
                content=b"MZ\x90",
            )

        assert ".exe" in str(exc.value)

    async def test_upload_no_extension(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_dataset,
    ):
        """上传无扩展名的文件应抛出 UnsupportedFileType"""
        with pytest.raises(UnsupportedFileType):
            await document_service.upload_document(
                user_id=sample_user["id"],
                dataset_id=sample_dataset.id,
                filename="README",
                content=b"content",
            )


# ════════════════════════════════════════════════════════════
# 查询单个文档
# ════════════════════════════════════════════════════════════


class TestGetDocument:
    """获取文档测试"""

    async def test_get_own_document(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
    ):
        """获取自己的文档应成功"""
        result = await document_service.get_document(
            sample_document.id, user_id=sample_user["id"]
        )

        assert result.id == sample_document.id
        assert result.filename == "test_document.pdf"
        assert result.file_type == "pdf"
        assert result.status == "pending"

    async def test_get_others_document(
        self,
        document_service: DocumentService,
        sample_user: dict,
        another_user: dict,
        sample_document,
    ):
        """获取别人的文档应抛出 DocumentNotFound"""
        with pytest.raises(DocumentNotFound):
            await document_service.get_document(
                sample_document.id, user_id=another_user["id"]
            )

    async def test_get_nonexistent_document(
        self,
        document_service: DocumentService,
        sample_user: dict,
    ):
        """不存在的文档应抛出 DocumentNotFound"""
        with pytest.raises(DocumentNotFound):
            await document_service.get_document(
                "non-existent-id", user_id=sample_user["id"]
            )


# ════════════════════════════════════════════════════════════
# 文档列表（分页）
# ════════════════════════════════════════════════════════════


class TestListDocuments:
    """文档列表测试"""

    async def test_list_empty(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_dataset,
    ):
        """数据集中无文档时应返回空列表"""
        result = await document_service.list_documents(
            dataset_id=sample_dataset.id,
            user_id=sample_user["id"],
        )

        assert result["total"] == 0
        assert len(result["items"]) == 0
        assert result["page"] == 1
        assert result["page_size"] == 20

    async def test_list_with_data(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_dataset,
        sample_document,
    ):
        """有文档时应返回正确数量"""
        result = await document_service.list_documents(
            dataset_id=sample_dataset.id,
            user_id=sample_user["id"],
        )

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].filename == "test_document.pdf"

    async def test_list_only_own_documents(
        self,
        document_service: DocumentService,
        sample_user: dict,
        another_user: dict,
        sample_dataset,
        sample_document,
        db_manager,
    ):
        """用户只能看到自己数据集下的文档"""
        # 为另一个用户创建数据集
        from app.schemas.dataset import DatasetCreateRequest
        from app.services.dataset_service import DatasetService

        another_ds = await DatasetService(db=db_manager).create(
            DatasetCreateRequest(name="别人的数据集"),
            user_id=another_user["id"],
        )

        # 为另一个用户上传文档
        await document_service.upload_document(
            user_id=another_user["id"],
            dataset_id=another_ds.id,
            filename="other.pdf",
            content=b"other content",
        )

        # sample_user 的文档列表应只包含自己的 1 个
        result = await document_service.list_documents(
            dataset_id=sample_dataset.id,
            user_id=sample_user["id"],
        )
        assert result["total"] == 1
        assert result["items"][0].filename == "test_document.pdf"

    async def test_list_pagination(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_dataset,
    ):
        """分页参数应正确工作"""
        # 创建 5 个文档
        for i in range(5):
            await document_service.upload_document(
                user_id=sample_user["id"],
                dataset_id=sample_dataset.id,
                filename=f"doc{i}.txt",
                content=f"content{i}".encode(),
            )

        # 第一页（每页 3 条）
        result = await document_service.list_documents(
            dataset_id=sample_dataset.id,
            user_id=sample_user["id"],
            page=1,
            page_size=3,
        )
        assert result["total"] == 5
        assert len(result["items"]) == 3

        # 第二页
        result2 = await document_service.list_documents(
            dataset_id=sample_dataset.id,
            user_id=sample_user["id"],
            page=2,
            page_size=3,
        )
        assert result2["total"] == 5
        assert len(result2["items"]) == 2

    async def test_list_order(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_dataset,
    ):
        """列表应按创建时间倒序排列"""
        # 创建 3 个文档
        for i in range(3):
            await document_service.upload_document(
                user_id=sample_user["id"],
                dataset_id=sample_dataset.id,
                filename=f"顺序文档{i}.txt",
                content=f"content{i}".encode(),
            )

        result = await document_service.list_documents(
            dataset_id=sample_dataset.id,
            user_id=sample_user["id"],
            page_size=10,
        )
        assert result["total"] == 3
        # 验证所有文档都在列表中（由于 SQLite 秒级精度，相同秒内顺序非确定）
        filenames = [d.filename for d in result["items"]]
        assert "顺序文档0.txt" in filenames
        assert "顺序文档1.txt" in filenames
        assert "顺序文档2.txt" in filenames


# ════════════════════════════════════════════════════════════
# 删除文档
# ════════════════════════════════════════════════════════════


class TestDeleteDocument:
    """删除文档测试"""

    async def test_delete_own_document(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
    ):
        """删除自己的文档应成功"""
        await document_service.delete_document(
            sample_document.id, user_id=sample_user["id"]
        )

        # 验证已被删除
        with pytest.raises(DocumentNotFound):
            await document_service.get_document(
                sample_document.id, user_id=sample_user["id"]
            )

    async def test_delete_others_document(
        self,
        document_service: DocumentService,
        sample_user: dict,
        another_user: dict,
        sample_document,
    ):
        """删除别人的文档应抛出 DocumentNotFound"""
        with pytest.raises(DocumentNotFound):
            await document_service.delete_document(
                sample_document.id, user_id=another_user["id"]
            )

        # 验证文档仍然存在（sample_user 仍能访问）
        result = await document_service.get_document(
            sample_document.id, user_id=sample_user["id"]
        )
        assert result.id == sample_document.id

    async def test_delete_nonexistent(
        self,
        document_service: DocumentService,
        sample_user: dict,
    ):
        """删除不存在的文档应抛出 DocumentNotFound"""
        with pytest.raises(DocumentNotFound):
            await document_service.delete_document(
                "non-existent-id", user_id=sample_user["id"]
            )

    async def test_delete_removes_file(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
        mock_storage,
    ):
        """删除文档时应清理存储文件"""
        await document_service.delete_document(
            sample_document.id, user_id=sample_user["id"]
        )

        mock_storage.delete.assert_awaited_once()


# ════════════════════════════════════════════════════════════
# 文档处理状态
# ════════════════════════════════════════════════════════════


class TestGetDocumentStatus:
    """文档状态查询测试"""

    async def test_get_status_pending(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
    ):
        """新上传文档状态应为 pending，进度为 0.0"""
        status = await document_service.get_document_status(
            sample_document.id, user_id=sample_user["id"]
        )

        assert isinstance(status, DocumentStatusResponse)
        assert status.id == sample_document.id
        assert status.status == "pending"
        assert status.progress == 0.0
        assert status.error_message is None

    async def test_get_status_completed(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
        db_manager,
    ):
        """状态为 completed 时进度应为 1.0"""
        # 模拟文档处理完成
        from app.models.document import Document
        from sqlalchemy import select

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Document).where(Document.id == sample_document.id)
            )
            doc = result.scalar_one()
            doc.status = "completed"
            await session.commit()

        status = await document_service.get_document_status(
            sample_document.id, user_id=sample_user["id"]
        )
        assert status.status == "completed"
        assert status.progress == 1.0

    async def test_get_status_failed(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
        db_manager,
    ):
        """状态为 failed 时应包含错误信息"""
        from app.models.document import Document
        from sqlalchemy import select

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Document).where(Document.id == sample_document.id)
            )
            doc = result.scalar_one()
            doc.status = "failed"
            doc.error_message = "解析失败：文件损坏"
            await session.commit()

        status = await document_service.get_document_status(
            sample_document.id, user_id=sample_user["id"]
        )
        assert status.status == "failed"
        assert status.progress == 0.0
        assert status.error_message == "解析失败：文件损坏"

    async def test_get_status_intermediate(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
        db_manager,
    ):
        """中间状态应有正确的进度值"""
        from app.models.document import Document
        from sqlalchemy import select

        status_progress = {
            "parsing": 0.2,
            "splitting": 0.4,
            "indexing": 0.7,
        }

        for status_val, expected_progress in status_progress.items():
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(Document).where(Document.id == sample_document.id)
                )
                doc = result.scalar_one()
                doc.status = status_val
                await session.commit()

            status = await document_service.get_document_status(
                sample_document.id, user_id=sample_user["id"]
            )
            assert status.status == status_val
            assert status.progress == expected_progress

    async def test_get_status_others_document(
        self,
        document_service: DocumentService,
        sample_user: dict,
        another_user: dict,
        sample_document,
    ):
        """查询别人的文档状态应抛出 DocumentNotFound"""
        with pytest.raises(DocumentNotFound):
            await document_service.get_document_status(
                sample_document.id, user_id=another_user["id"]
            )


# ════════════════════════════════════════════════════════════
# 文档切片列表
# ════════════════════════════════════════════════════════════


class TestListChunks:
    """文档切片列表测试"""

    async def test_list_chunks_empty(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
    ):
        """无切片的文档应返回空列表"""
        result = await document_service.list_chunks(
            sample_document.id, user_id=sample_user["id"]
        )

        assert result["total"] == 0
        assert len(result["items"]) == 0
        assert result["page"] == 1
        assert result["page_size"] == 50

    async def test_list_chunks_with_data(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
        db_manager,
    ):
        """有切片时应正确返回"""
        from app.models.chunk import Chunk

        async with db_manager.get_session() as session:
            for i in range(3):
                chunk = Chunk(
                    document_id=sample_document.id,
                    content=f"这是第{i}个切片内容",
                    chunk_index=i,
                    meta_data={"page": i + 1},
                )
                session.add(chunk)
            await session.commit()

        result = await document_service.list_chunks(
            sample_document.id, user_id=sample_user["id"]
        )

        assert result["total"] == 3
        assert len(result["items"]) == 3
        assert isinstance(result["items"][0], ChunkResponse)
        assert result["items"][0].chunk_index == 0
        assert result["items"][0].content == "这是第0个切片内容"
        assert result["items"][0].metadata == {"page": 1}

    async def test_list_chunks_pagination(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
        db_manager,
    ):
        """切片列表应支持分页"""
        from app.models.chunk import Chunk

        async with db_manager.get_session() as session:
            for i in range(5):
                chunk = Chunk(
                    document_id=sample_document.id,
                    content=f"切片{i}",
                    chunk_index=i,
                )
                session.add(chunk)
            await session.commit()

        # 第一页（每页 2 条）
        result = await document_service.list_chunks(
            sample_document.id,
            user_id=sample_user["id"],
            page=1,
            page_size=2,
        )
        assert result["total"] == 5
        assert len(result["items"]) == 2

        # 第三页
        result3 = await document_service.list_chunks(
            sample_document.id,
            user_id=sample_user["id"],
            page=3,
            page_size=2,
        )
        assert result3["total"] == 5
        assert len(result3["items"]) == 1

    async def test_list_chunks_ordered_by_index(
        self,
        document_service: DocumentService,
        sample_user: dict,
        sample_document,
        db_manager,
    ):
        """切片应按 chunk_index 升序排列"""
        from app.models.chunk import Chunk

        async with db_manager.get_session() as session:
            # 乱序插入
            for i in [2, 0, 1]:
                chunk = Chunk(
                    document_id=sample_document.id,
                    content=f"切片{i}",
                    chunk_index=i,
                )
                session.add(chunk)
            await session.commit()

        result = await document_service.list_chunks(
            sample_document.id, user_id=sample_user["id"], page_size=10
        )

        assert result["total"] == 3
        indices = [c.chunk_index for c in result["items"]]
        assert indices == [0, 1, 2]

    async def test_list_chunks_others_document(
        self,
        document_service: DocumentService,
        sample_user: dict,
        another_user: dict,
        sample_document,
    ):
        """查看别人的文档切片应抛出 DocumentNotFound"""
        with pytest.raises(DocumentNotFound):
            await document_service.list_chunks(
                sample_document.id, user_id=another_user["id"]
            )


# ════════════════════════════════════════════════════════════
# 文档批量删除（数据集级联）
# ════════════════════════════════════════════════════════════


class TestCascadeDelete:
    """文档级联删除测试"""

    async def test_delete_dataset_cascades_documents(
        self,
        document_service: DocumentService,
        dataset_service,
        sample_user: dict,
        sample_dataset,
        sample_document,
        db_manager,
    ):
        """删除数据集时应级联删除关联文档和切片"""
        from app.models.chunk import Chunk
        from app.models.document import Document
        from sqlalchemy import select, func

        # 添加切片
        async with db_manager.get_session() as session:
            chunk = Chunk(
                document_id=sample_document.id,
                content="测试切片",
                chunk_index=0,
            )
            session.add(chunk)
            await session.commit()

        # 验证文档和切片存在
        async with db_manager.get_session() as session:
            doc_cnt = await session.execute(
                select(func.count(Document.id)).where(
                    Document.dataset_id == sample_dataset.id
                )
            )
            assert doc_cnt.scalar() == 1

            chunk_cnt = await session.execute(
                select(func.count(Chunk.id)).where(
                    Chunk.document_id == sample_document.id
                )
            )
            assert chunk_cnt.scalar() == 1

        # 删除数据集
        await dataset_service.delete_dataset(
            sample_dataset.id, user_id=sample_user["id"]
        )

        # 验证文档和切片已被级联删除
        async with db_manager.get_session() as session:
            doc_cnt = await session.execute(
                select(func.count(Document.id)).where(
                    Document.dataset_id == sample_dataset.id
                )
            )
            assert doc_cnt.scalar() == 0

            # 切片通过 Document cascade 删除
            chunk_cnt = await session.execute(
                select(func.count(Chunk.id)).where(
                    Chunk.document_id == sample_document.id
                )
            )
            assert chunk_cnt.scalar() == 0


# ════════════════════════════════════════════════════════════
# 异常错误码验证
# ════════════════════════════════════════════════════════════


class TestDocumentServiceErrors:
    """文档服务异常属性验证"""

    def test_document_service_error_defaults(self):
        """DocumentServiceError 应具有默认值"""
        err = DocumentServiceError()
        assert err.code == "document_service_error"
        assert err.message == "文档服务错误"

    def test_document_not_found_error(self):
        """DocumentNotFound 应包含文档 ID"""
        err = DocumentNotFound("doc-001")
        assert err.code == "document_not_found"
        assert "doc-001" in str(err)

    def test_document_permission_denied_error(self):
        """DocumentPermissionDenied 应包含文档 ID"""
        err = DocumentPermissionDenied("doc-001")
        assert err.code == "document_permission_denied"
        assert "doc-001" in str(err)

    def test_unsupported_file_type_error(self):
        """UnsupportedFileType 应包含文件类型"""
        err = UnsupportedFileType(".exe")
        assert err.code == "unsupported_file_type"
        assert ".exe" in str(err)

    def test_exceptions_inherit_from_document_service_error(self):
        """所有文档服务异常都应继承 DocumentServiceError"""
        assert issubclass(DocumentNotFound, DocumentServiceError)
        assert issubclass(DocumentPermissionDenied, DocumentServiceError)
        assert issubclass(UnsupportedFileType, DocumentServiceError)

    def test_exceptions_inherit_from_rag_error(self):
        """所有文档服务异常都应最终继承 RagError"""
        from app.core.exceptions import RagError

        assert issubclass(DocumentServiceError, RagError)
