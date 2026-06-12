"""用户 API 路由测试

覆盖：
- GET /api/v1/users/me — 获取当前用户信息
- PUT /api/v1/users/me — 更新个人信息
- PUT /api/v1/users/me/password — 修改密码
"""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.services.user_service import (
    PasswordNotMatch,
    UserAlreadyExists,
    UserNotFound,
)


class TestGetCurrentUser:
    """获取当前用户测试"""

    async def test_get_current_user_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """获取当前用户应返回用户信息"""
        resp = await client.get("/api/v1/users/me", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["username"] == "testuser"
        assert data["data"]["email"] == "test@example.com"


class TestUpdateCurrentUser:
    """更新个人信息测试"""

    async def test_update_email_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """更新邮箱应返回 200"""
        payload = {"email": "newemail@example.com"}
        resp = await client.put(
            "/api/v1/users/me", json=payload, headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"

    async def test_update_email_conflict(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """邮箱冲突应返回 409"""
        mock_container.user_service.update_user = AsyncMock(
            side_effect=UserAlreadyExists("邮箱", "existing@example.com")
        )
        payload = {"email": "existing@example.com"}
        resp = await client.put(
            "/api/v1/users/me", json=payload, headers=auth_header
        )
        assert resp.status_code == 409

    async def test_update_user_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """用户不存在应返回 404"""
        mock_container.user_service.update_user = AsyncMock(
            side_effect=UserNotFound("nonexistent")
        )
        payload = {"email": "any@example.com"}
        resp = await client.put(
            "/api/v1/users/me", json=payload, headers=auth_header
        )
        assert resp.status_code == 404


class TestChangePassword:
    """修改密码测试"""

    async def test_change_password_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """修改密码应返回 200"""
        payload = {
            "old_password": "oldpass123",
            "new_password": "newpass456",
        }
        resp = await client.put(
            "/api/v1/users/me/password", json=payload, headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "密码修改成功"

    async def test_change_password_wrong_old(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """原密码错误应返回 400"""
        mock_container.user_service.change_password = AsyncMock(
            side_effect=PasswordNotMatch()
        )
        payload = {
            "old_password": "wrong",
            "new_password": "newpass456",
        }
        resp = await client.put(
            "/api/v1/users/me/password", json=payload, headers=auth_header
        )
        assert resp.status_code == 400

    async def test_change_password_user_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """用户不存在应返回 404"""
        mock_container.user_service.change_password = AsyncMock(
            side_effect=UserNotFound("nonexistent")
        )
        payload = {
            "old_password": "oldpass",
            "new_password": "newpass",
        }
        resp = await client.put(
            "/api/v1/users/me/password", json=payload, headers=auth_header
        )
        assert resp.status_code == 404
