"""用户 Pydantic 模式单元测试"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.user import (
    PasswordChangeRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)


class TestUserRegisterRequest:
    """用户注册请求校验测试"""

    def test_valid_request(self):
        """正常注册请求应通过校验"""
        data = UserRegisterRequest(
            username="testuser",
            email="test@example.com",
            password="secure123",
        )
        assert data.username == "testuser"
        assert data.email == "test@example.com"

    def test_username_too_short(self):
        """用户名过短应拒绝"""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="a",
                email="test@example.com",
                password="secure123",
            )

    def test_username_too_long(self):
        """用户名过长应拒绝"""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="a" * 51,
                email="test@example.com",
                password="secure123",
            )

    def test_username_invalid_chars(self):
        """用户名含非法字符应拒绝"""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="user name!",
                email="test@example.com",
                password="secure123",
            )

    def test_password_too_short(self):
        """密码过短应拒绝"""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="testuser",
                email="test@example.com",
                password="12345",
            )

    def test_invalid_email(self):
        """非法邮箱格式应拒绝"""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="testuser",
                email="not-an-email",
                password="secure123",
            )


class TestUserLoginRequest:
    """用户登录请求校验测试"""

    def test_valid_login(self):
        """正常登录请求应通过校验"""
        data = UserLoginRequest(
            username="testuser", password="secure123"
        )
        assert data.username == "testuser"

    def test_empty_username(self):
        """空用户名应拒绝"""
        with pytest.raises(ValidationError):
            UserLoginRequest(username="", password="secure123")


class TestUserResponse:
    """用户响应序列化测试"""

    def test_valid_response(self):
        """正常用户响应应可构造"""
        now = datetime.now()
        data = UserResponse(
            id="uuid-123",
            username="testuser",
            email="test@example.com",
            role="user",
            is_active=True,
            created_at=now,
        )
        assert data.id == "uuid-123"
        assert data.is_active is True

    def test_from_attributes(self):
        """应支持 from_attributes 模式（ORM 兼容）"""
        assert UserResponse.model_config.get("from_attributes") is True

    def test_default_is_active(self):
        """验证可选的 created_at 可为 None"""
        data = UserResponse(
            id="uuid-123",
            username="testuser",
            email="test@example.com",
            role="admin",
            is_active=False,
        )
        assert data.role == "admin"
        assert data.is_active is False
        assert data.created_at is None


class TestUserUpdateRequest:
    """用户更新请求校验测试"""

    def test_valid_update(self):
        """正常更新请求应通过校验"""
        data = UserUpdateRequest(email="new@example.com")
        assert data.email == "new@example.com"

    def test_optional_email(self):
        """email 字段应为可选"""
        data = UserUpdateRequest()
        assert data.email is None


class TestPasswordChangeRequest:
    """密码修改请求校验测试"""

    def test_valid_request(self):
        """正常密码修改请求应通过校验"""
        data = PasswordChangeRequest(
            old_password="old123", new_password="new456"
        )
        assert data.old_password == "old123"

    def test_new_password_too_short(self):
        """新密码过短应拒绝"""
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                old_password="old123", new_password="new"
            )


class TestTokenResponse:
    """令牌响应测试"""

    def test_valid_token_response(self):
        """正常令牌响应应可构造"""
        user = UserResponse(
            id="uuid-123",
            username="testuser",
            email="test@example.com",
            role="user",
            is_active=True,
        )
        data = TokenResponse(
            access_token="eyJhbGci...",
            token_type="bearer",
            user=user,
        )
        assert data.token_type == "bearer"
        assert data.user.username == "testuser"
