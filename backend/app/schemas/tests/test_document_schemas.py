"""文档 Pydantic 模式单元测试"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.document import DocumentResponse, DocumentStatusResponse


class TestDocumentResponse:
    """文档响应序列化测试"""

    def test_valid_response(self):
        """正常文档响应应可构造"""
        now = datetime.now()
        data = DocumentResponse(
            id="uuid-doc-1",
            filename="report.pdf",
            file_type="pdf",
            file_size=1024000,
            status="completed",
            error_message=None,
            dataset_id="uuid-ds-1",
            chunk_count=10,
            created_at=now,
            updated_at=now,
        )
        assert data.filename == "report.pdf"
        assert data.file_type == "pdf"
        assert data.file_size == 1024000
        assert data.status == "completed"
        assert data.chunk_count == 10

    def test_from_attributes(self):
        """应支持 from_attributes 模式"""
        assert DocumentResponse.model_config.get("from_attributes") is True

    def test_with_error(self):
        """含错误信息的文档响应"""
        now = datetime.now()
        data = DocumentResponse(
            id="uuid-doc-2",
            filename="broken.docx",
            file_type="docx",
            file_size=500,
            status="failed",
            error_message="格式不支持",
            dataset_id=None,
            chunk_count=0,
            created_at=now,
            updated_at=now,
        )
        assert data.error_message == "格式不支持"
        assert data.dataset_id is None

    def test_negative_file_size(self):
        """文件大小不应为负"""
        now = datetime.now()
        with pytest.raises(ValidationError):
            DocumentResponse(
                id="uuid-doc-3",
                filename="bad.txt",
                file_type="txt",
                file_size=-1,
                status="pending",
                dataset_id=None,
                chunk_count=0,
                created_at=now,
                updated_at=now,
            )


class TestDocumentStatusResponse:
    """文档状态响应测试"""

    def test_valid_status(self):
        """正常状态响应应可构造"""
        data = DocumentStatusResponse(
            id="uuid-doc-1",
            status="processing",
            progress=0.5,
        )
        assert data.status == "processing"
        assert data.progress == 0.5

    def test_progress_bounds(self):
        """进度值必须在 0~1 之间"""
        with pytest.raises(ValidationError):
            DocumentStatusResponse(
                id="uuid-doc-1",
                status="processing",
                progress=1.5,
            )

        with pytest.raises(ValidationError):
            DocumentStatusResponse(
                id="uuid-doc-1",
                status="processing",
                progress=-0.1,
            )

    def test_with_error(self):
        """含错误信息的状态响应"""
        data = DocumentStatusResponse(
            id="uuid-doc-2",
            status="failed",
            progress=0.0,
            error_message="解析失败",
        )
        assert data.error_message == "解析失败"
