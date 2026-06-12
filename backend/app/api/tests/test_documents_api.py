"""文档 API 路由测试

覆盖：
- GET /datasets/{dataset_id}/documents — 文档列表
- POST /datasets/{dataset_id}/documents — 上传文档
- GET /documents/{id} — 文档详情
- DELETE /documents/{id} — 删除文档
- GET /documents/{id}/chunks — 切片列表
- GET /documents/{id}/status — 处理状态
- 鉴权保护
"""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.services.document_service import (
    DocumentNotFound,
    UnsupportedFileType,
)


class TestListDocuments:
    """文档列表测试"""

    async def test_list_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """获取文档列表应返回 200"""
        resp = await client.get(
            "/api/v1/datasets/dataset-001/documents",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["total"] == 1

    async def test_list_with_pagination(
        self, client: AsyncClient, auth_header: dict
    ):
        """分页参数应正确传递"""
        resp = await client.get(
            "/api/v1/datasets/dataset-001/documents?page=1&page_size=10",
            headers=auth_header,
        )
        assert resp.status_code == 200


class TestUploadDocument:
    """文档上传测试"""

    async def test_upload_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """正常上传文档应返回 201"""
        files = {"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")}
        resp = await client.post(
            "/api/v1/datasets/dataset-001/documents",
            files=files,
            headers=auth_header,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == 201
        assert data["message"] == "文档上传成功，正在处理"
        assert data["data"]["filename"] == "test.pdf"

    async def test_upload_unsupported_type(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不支持的文件类型应返回 400"""
        mock_container.document_service.upload_document = AsyncMock(
            side_effect=UnsupportedFileType(".xyz")
        )
        files = {
            "file": ("test.xyz", b"some content", "application/octet-stream")
        }
        resp = await client.post(
            "/api/v1/datasets/dataset-001/documents",
            files=files,
            headers=auth_header,
        )
        assert resp.status_code == 400


class TestGetDocument:
    """文档详情测试"""

    async def test_get_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """获取文档详情应返回 200"""
        resp = await client.get(
            "/api/v1/documents/doc-001", headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == "doc-001"

    async def test_get_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的文档应返回 404"""
        mock_container.document_service.get_document = AsyncMock(
            side_effect=DocumentNotFound("nonexistent")
        )
        resp = await client.get(
            "/api/v1/documents/nonexistent", headers=auth_header
        )
        assert resp.status_code == 404


class TestDeleteDocument:
    """删除文档测试"""

    async def test_delete_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """删除文档应返回 200"""
        resp = await client.delete(
            "/api/v1/documents/doc-001", headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "文档已删除"

    async def test_delete_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的文档应返回 404"""
        mock_container.document_service.delete_document = AsyncMock(
            side_effect=DocumentNotFound("nonexistent")
        )
        resp = await client.delete(
            "/api/v1/documents/nonexistent", headers=auth_header
        )
        assert resp.status_code == 404


class TestGetDocumentStatus:
    """文档处理状态测试"""

    async def test_status_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """获取处理状态应返回 200"""
        resp = await client.get(
            "/api/v1/documents/doc-001/status", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["id"] == "doc-001"
        assert data["data"]["status"] == "completed"
        assert data["data"]["progress"] == 1.0

    async def test_status_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的文档应返回 404"""
        mock_container.document_service.get_document_status = AsyncMock(
            side_effect=DocumentNotFound("nonexistent")
        )
        resp = await client.get(
            "/api/v1/documents/nonexistent/status", headers=auth_header
        )
        assert resp.status_code == 404


class TestListChunks:
    """文档切片列表测试"""

    async def test_chunks_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """获取切片列表应返回 200"""
        resp = await client.get(
            "/api/v1/documents/doc-001/chunks", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data["data"]

    async def test_chunks_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的文档应返回 404"""
        mock_container.document_service.list_chunks = AsyncMock(
            side_effect=DocumentNotFound("nonexistent")
        )
        resp = await client.get(
            "/api/v1/documents/nonexistent/chunks", headers=auth_header
        )
        assert resp.status_code == 404
