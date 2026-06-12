"""API 路由测试夹具

提供：
- FastAPI TestClient（挂载 v1 路由）
- Mock Container（覆盖所有服务）
- 预置的测试 Token
- 初始化好的数据库与真实服务（用于集成测试）
"""

from typing import Callable, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.container import Container
from app.api.errors import register_exception_handlers
from app.api.v1 import v1_router
from app.schemas.admin import SystemStatsResponse
from app.schemas.conversation import ConversationResponse, MessageResponse
from app.schemas.dataset import DatasetResponse
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.schemas.user import TokenResponse, UserResponse


# ════════════════════════════════════════════════════════════
# 辅助函数
# ════════════════════════════════════════════════════════════


def create_mock_response(model_class, **overrides) -> Callable:
    """返回一个工厂函数，用于创建具有给定覆盖值的 mock 响应"""
    def factory(**kwargs) -> dict:
        merged = {**overrides, **kwargs}
        return model_class(**merged)
    return factory


# ════════════════════════════════════════════════════════════
# Mock 容器
# ════════════════════════════════════════════════════════════


@pytest.fixture
def mock_user_response() -> dict:
    """标准用户响应"""
    return {
        "id": "user-001",
        "username": "testuser",
        "email": "test@example.com",
        "role": "user",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00",
    }


@pytest.fixture
def mock_admin_user_response() -> dict:
    """管理员用户响应"""
    return {
        "id": "admin-001",
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00",
    }


@pytest.fixture
def mock_token_response() -> dict:
    """令牌响应"""
    return {
        "access_token": "mock-jwt-token",
        "token_type": "bearer",
        "user": {
            "id": "user-001",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "is_active": True,
            "created_at": "2026-01-01T00:00:00",
        },
    }


def _create_mock_container(
    user_response: Optional[dict] = None,
    admin_mode: bool = False,
):
    """创建模拟的 DI 容器

    所有服务方法均为 AsyncMock，可随时通过 ``.return_value`` 或
    ``.side_effect`` 控制返回值。
    """
    container = MagicMock(spec=Container)

    # ── Security ──
    security = MagicMock()
    payload = {
        "sub": "admin-001" if admin_mode else "user-001",
        "role": "admin" if admin_mode else "user",
    }
    security.verify_token = MagicMock(return_value=payload)
    container.security = security

    # ── UserService ──
    user_svc = MagicMock()
    ur = user_response or {
        "id": "admin-001" if admin_mode else "user-001",
        "username": "admin" if admin_mode else "testuser",
        "email": "admin@example.com" if admin_mode else "test@example.com",
        "role": "admin" if admin_mode else "user",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00",
    }
    user_response_obj = UserResponse(**ur)

    user_svc.register = AsyncMock(return_value=user_response_obj)
    user_svc.login = AsyncMock(
        return_value=TokenResponse(
            access_token="mock-jwt-token",
            token_type="bearer",
            user=user_response_obj,
        )
    )
    user_svc.get_user_by_id = AsyncMock(return_value=user_response_obj)
    user_svc.update_user = AsyncMock(return_value=user_response_obj)
    user_svc.change_password = AsyncMock(return_value=None)
    container.user_service = user_svc

    # ── DatasetService ──
    ds_svc = MagicMock()
    dataset_resp = DatasetResponse(
        id="dataset-001",
        name="测试数据集",
        description="这是一个测试数据集",
        document_count=0,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )
    ds_svc.create = AsyncMock(return_value=dataset_resp)
    ds_svc.get_dataset = AsyncMock(return_value=dataset_resp)
    ds_svc.list_datasets = AsyncMock(return_value=([dataset_resp], 1))
    ds_svc.update_dataset = AsyncMock(return_value=dataset_resp)
    ds_svc.delete_dataset = AsyncMock(return_value=None)
    container.dataset_service = ds_svc

    # ── DocumentService ──
    doc_svc = MagicMock()
    doc_resp = DocumentResponse(
        id="doc-001",
        filename="test.pdf",
        file_type="pdf",
        file_size=1024,
        status="completed",
        dataset_id="dataset-001",
        chunk_count=5,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )
    status_resp = DocumentStatusResponse(
        id="doc-001",
        status="completed",
        progress=1.0,
    )
    doc_svc.upload_document = AsyncMock(return_value=doc_resp)
    doc_svc.get_document = AsyncMock(return_value=doc_resp)
    doc_svc.list_documents = AsyncMock(
        return_value={
            "items": [doc_resp],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
    )
    doc_svc.delete_document = AsyncMock(return_value=None)
    doc_svc.get_document_status = AsyncMock(return_value=status_resp)
    doc_svc.list_chunks = AsyncMock(
        return_value={
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 50,
        }
    )
    container.document_service = doc_svc

    # ── ConversationService ──
    conv_svc = MagicMock()
    conv_resp = ConversationResponse(
        id="conv-001",
        title="测试对话",
        dataset_id=None,
        message_count=0,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )
    msg_resp = MessageResponse(
        id="msg-001",
        role="assistant",
        content="测试回答",
        sources=[],
        created_at="2026-01-01T00:00:00",
    )
    conv_svc.create_conversation = AsyncMock(return_value=conv_resp)
    conv_svc.get_conversation = AsyncMock(return_value=conv_resp)
    conv_svc.list_conversations = AsyncMock(
        return_value={
            "items": [conv_resp],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
    )
    conv_svc.delete_conversation = AsyncMock(return_value=None)
    conv_svc.get_messages = AsyncMock(
        return_value={
            "items": [msg_resp],
            "total": 1,
            "page": 1,
            "page_size": 50,
        }
    )

    # send_message 是一个异步生成器
    async def _mock_send_message(*args, **kwargs):
        yield {"type": "delta", "content": "这是"}
        yield {"type": "delta", "content": "一个"}
        yield {"type": "delta", "content": "测试回答"}
        yield {"type": "sources", "content": []}
        yield {"type": "done", "message_id": "msg-001"}

    conv_svc.send_message = _mock_send_message
    container.conversation_service = conv_svc

    # ── AdminService ──
    admin_svc = MagicMock()
    admin_svc.list_users = AsyncMock(
        return_value={
            "users": [
                UserResponse(
                    id="user-001",
                    username="testuser",
                    email="test@example.com",
                    role="user",
                    is_active=True,
                    created_at="2026-01-01T00:00:00",
                )
            ],
            "total": 1,
        }
    )
    admin_svc.get_stats = AsyncMock(
        return_value=SystemStatsResponse(
            total_users=10,
            total_documents=100,
            total_conversations=50,
            total_chunks=5000,
            active_users_today=3,
        )
    )
    container.admin_service = admin_svc

    return container


@pytest.fixture
def mock_container(mock_user_response: dict):
    """返回默认的 mock 容器（普通用户）"""
    return _create_mock_container(user_response=mock_user_response, admin_mode=False)


@pytest.fixture
def mock_admin_container(mock_admin_user_response: dict):
    """返回 mock 容器（管理员）"""
    return _create_mock_container(
        user_response=mock_admin_user_response, admin_mode=True
    )


# ════════════════════════════════════════════════════════════
# FastAPI App + TestClient
# ════════════════════════════════════════════════════════════


@pytest.fixture
def app(mock_container: Container) -> FastAPI:
    """创建 FastAPI 测试应用（依赖已被 mock 覆盖）"""
    application = FastAPI(title="MyRAG Test")
    application.include_router(v1_router)
    register_exception_handlers(application)

    # 覆盖依赖
    from app.api.deps import get_container

    async def _override_container():
        return mock_container

    application.dependency_overrides[get_container] = _override_container

    return application


@pytest.fixture
def admin_app(mock_admin_container: Container) -> FastAPI:
    """创建 FastAPI 测试应用（管理员模式）"""
    application = FastAPI(title="MyRAG Test Admin")
    application.include_router(v1_router)
    register_exception_handlers(application)

    from app.api.deps import get_container

    async def _override_container():
        return mock_admin_container

    application.dependency_overrides[get_container] = _override_container

    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """返回 HTTP 测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_client(admin_app: FastAPI) -> AsyncClient:
    """返回 HTTP 测试客户端（管理员）"""
    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_header() -> dict:
    """标准用户的认证头"""
    return {"Authorization": "Bearer mock-jwt-token"}


@pytest.fixture
def admin_auth_header() -> dict:
    """管理员的认证头"""
    return {"Authorization": "Bearer mock-admin-token"}


# ════════════════════════════════════════════════════════════
# 集成测试：真实数据库 + 真实服务
# ════════════════════════════════════════════════════════════


@pytest.fixture(scope="function")
def integration_app():
    """创建 FastAPI 应用（使用真实依赖覆盖）—— 用于集成测试"""
    application = FastAPI(title="MyRAG Integration Test")
    application.include_router(v1_router)
    register_exception_handlers(application)
    return application
