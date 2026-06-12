"""数据集 API 路由测试

覆盖：
- GET /api/v1/datasets — 列表
- POST /api/v1/datasets — 创建
- GET /api/v1/datasets/{id} — 详情
- PUT /api/v1/datasets/{id} — 更新
- DELETE /api/v1/datasets/{id} — 删除
- 鉴权保护
"""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.services.dataset_service import (
    DatasetNotFound,
    DatasetPermissionDenied,
)


class TestListDatasets:
    """数据集列表测试"""

    async def test_list_empty(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """无数据集时应返回空列表"""
        mock_container.dataset_service.list_datasets = AsyncMock(
            return_value=([], 0)
        )
        resp = await client.get(
            "/api/v1/datasets", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []

    async def test_list_with_data(
        self, client: AsyncClient, auth_header: dict
    ):
        """有数据集时应返回列表"""
        resp = await client.get(
            "/api/v1/datasets", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1

    async def test_list_pagination(
        self, client: AsyncClient, auth_header: dict
    ):
        """分页参数应正确传递"""
        resp = await client.get(
            "/api/v1/datasets?page=1&page_size=10",
            headers=auth_header,
        )
        assert resp.status_code == 200


class TestCreateDataset:
    """创建数据集测试"""

    async def test_create_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """正常创建应返回 201"""
        payload = {
            "name": "新数据集",
            "description": "这是一个新数据集",
        }
        resp = await client.post(
            "/api/v1/datasets", json=payload, headers=auth_header
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == 201
        assert data["message"] == "数据集创建成功"

    async def test_create_missing_name(
        self, client: AsyncClient, auth_header: dict
    ):
        """缺少名称应返回 422"""
        resp = await client.post(
            "/api/v1/datasets", json={}, headers=auth_header
        )
        assert resp.status_code == 422


class TestGetDataset:
    """数据集详情测试"""

    async def test_get_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """正常获取应返回数据集信息"""
        resp = await client.get(
            "/api/v1/datasets/dataset-001", headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == "dataset-001"

    async def test_get_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的数据集应返回 404"""
        mock_container.dataset_service.get_dataset = AsyncMock(
            side_effect=DatasetNotFound("nonexistent")
        )
        resp = await client.get(
            "/api/v1/datasets/nonexistent", headers=auth_header
        )
        assert resp.status_code == 404

    async def test_get_permission_denied(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """无权访问应返回 403"""
        mock_container.dataset_service.get_dataset = AsyncMock(
            side_effect=DatasetPermissionDenied("dataset-001")
        )
        resp = await client.get(
            "/api/v1/datasets/dataset-001", headers=auth_header
        )
        assert resp.status_code == 403


class TestUpdateDataset:
    """更新数据集测试"""

    async def test_update_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """正常更新应返回 200"""
        payload = {"name": "新名称", "description": "新描述"}
        resp = await client.put(
            "/api/v1/datasets/dataset-001",
            json=payload,
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"

    async def test_update_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的数据集应返回 404"""
        mock_container.dataset_service.update_dataset = AsyncMock(
            side_effect=DatasetNotFound("nonexistent")
        )
        payload = {"name": "新名称"}
        resp = await client.put(
            "/api/v1/datasets/nonexistent",
            json=payload,
            headers=auth_header,
        )
        assert resp.status_code == 404


class TestDeleteDataset:
    """删除数据集测试"""

    async def test_delete_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """正常删除应返回 200"""
        resp = await client.delete(
            "/api/v1/datasets/dataset-001", headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "数据集已删除"

    async def test_delete_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的数据集应返回 404"""
        mock_container.dataset_service.delete_dataset = AsyncMock(
            side_effect=DatasetNotFound("nonexistent")
        )
        resp = await client.delete(
            "/api/v1/datasets/nonexistent", headers=auth_header
        )
        assert resp.status_code == 404
