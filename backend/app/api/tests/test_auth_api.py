"""认证 API 路由测试

覆盖：
- POST /api/v1/auth/register — 正常注册、重复注册、参数校验
- POST /api/v1/auth/login — 正常登录、密码错误、用户禁用
- POST /api/v1/auth/refresh — 暂未实现
- 无 Token 访问受保护接口 → 401
"""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.services.user_service import (
    InvalidCredentials,
    UserAlreadyExists,
    UserInactive,
)


class TestRegister:
    """注册接口测试"""

    async def test_register_success(self, client: AsyncClient):
        """正常注册应返回 201 和用户信息"""
        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "secure123",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == 201
        assert data["message"] == "注册成功"
        assert data["data"]["username"] == "testuser"

    async def test_register_duplicate(
        self, client: AsyncClient, mock_container
    ):
        """重复用户名或邮箱应返回 409"""
        mock_container.user_service.register = AsyncMock(
            side_effect=UserAlreadyExists("用户名", "testuser")
        )
        payload = {
            "username": "testuser",
            "email": "other@example.com",
            "password": "secure123",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409
        assert "已被注册" in resp.json()["message"]

    async def test_register_missing_fields(self, client: AsyncClient):
        """缺少必填字段应返回 422"""
        resp = await client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        """无效邮箱应返回 422"""
        payload = {
            "username": "newuser",
            "email": "not-an-email",
            "password": "secure123",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422


class TestLogin:
    """登录接口测试"""

    async def test_login_success(self, client: AsyncClient):
        """正常登录应返回 200 和 JWT 令牌"""
        payload = {"username": "testuser", "password": "secure123"}
        resp = await client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["message"] == "登录成功"
        assert data["data"]["access_token"] == "mock-jwt-token"
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["user"]["username"] == "testuser"

    async def test_login_wrong_password(
        self, client: AsyncClient, mock_container
    ):
        """错误密码应返回 401"""
        mock_container.user_service.login = AsyncMock(
            side_effect=InvalidCredentials()
        )
        payload = {"username": "testuser", "password": "wrongpass"}
        resp = await client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 401
        assert "用户名或密码错误" in resp.json()["message"]

    async def test_login_inactive_user(
        self, client: AsyncClient, mock_container
    ):
        """被禁用的用户应返回 403"""
        mock_container.user_service.login = AsyncMock(
            side_effect=UserInactive()
        )
        payload = {"username": "disabled", "password": "pass123"}
        resp = await client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 403
        assert "禁用" in resp.json()["message"]

    async def test_login_missing_fields(self, client: AsyncClient):
        """缺少字段应返回 422"""
        resp = await client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422


class TestRefreshToken:
    """Token 刷新接口测试"""

    async def test_refresh_not_implemented(self, client: AsyncClient):
        """刷新接口目前应返回 501"""
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 501


class TestAuthProtection:
    """鉴权保护测试"""

    async def test_no_token_returns_401(self, client: AsyncClient):
        """未携带 Token 访问受保护接口应返回 401"""
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401

    async def test_protected_route_with_valid_token(
        self, client: AsyncClient, auth_header: dict
    ):
        """携带有效 Token 可访问受保护接口"""
        resp = await client.get(
            "/api/v1/users/me", headers=auth_header
        )
        assert resp.status_code == 200

    async def test_admin_endpoint_without_admin(
        self, client: AsyncClient, auth_header: dict
    ):
        """非管理员访问 admin 接口应返回 403"""
        resp = await client.get(
            "/api/v1/admin/stats", headers=auth_header
        )
        assert resp.status_code == 403

    async def test_admin_endpoint_with_admin(
        self, admin_client: AsyncClient, admin_auth_header: dict
    ):
        """管理员访问 admin 接口应成功"""
        resp = await admin_client.get(
            "/api/v1/admin/stats", headers=admin_auth_header
        )
        assert resp.status_code == 200
