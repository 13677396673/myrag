"""数据集 Pydantic 模式单元测试"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.dataset import (
    DatasetCreateRequest,
    DatasetResponse,
    DatasetUpdateRequest,
)


class TestDatasetCreateRequest:
    """数据集创建请求校验测试"""

    def test_valid_request_with_name_only(self):
        """仅填名称的请求应通过校验"""
        data = DatasetCreateRequest(name="我的数据集")
        assert data.name == "我的数据集"
        assert data.description is None

    def test_valid_request_with_all_fields(self):
        """填所有字段的请求应通过校验"""
        data = DatasetCreateRequest(
            name="知识库", description="公司内部文档知识库"
        )
        assert data.name == "知识库"
        assert data.description == "公司内部文档知识库"

    def test_name_empty(self):
        """空名称应拒绝"""
        with pytest.raises(ValidationError):
            DatasetCreateRequest(name="")

    def test_name_too_long(self):
        """名称过长应拒绝"""
        with pytest.raises(ValidationError):
            DatasetCreateRequest(name="a" * 256)


class TestDatasetUpdateRequest:
    """数据集更新请求校验测试"""

    def test_valid_update(self):
        """正常更新请求应通过校验"""
        data = DatasetUpdateRequest(
            name="新名称", description="新描述"
        )
        assert data.name == "新名称"

    def test_all_optional(self):
        """所有字段均应为可选"""
        data = DatasetUpdateRequest()
        assert data.name is None
        assert data.description is None


class TestDatasetResponse:
    """数据集响应序列化测试"""

    def test_valid_response(self):
        """正常数据集响应应可构造"""
        now = datetime.now()
        data = DatasetResponse(
            id="uuid-456",
            name="知识库",
            description="说明",
            document_count=5,
            created_at=now,
            updated_at=now,
        )
        assert data.id == "uuid-456"
        assert data.document_count == 5

    def test_from_attributes(self):
        """应支持 from_attributes 模式"""
        assert DatasetResponse.model_config.get("from_attributes") is True
