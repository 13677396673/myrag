"""安全模块测试用例

测试密码哈希/验证的往返、JWT 创建/验证的往返、过期/无效 token 等场景。
所有测试使用 ``Settings(JWT_SECRET_KEY="test-secret")``，不依赖真实数据库。
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import pytest
from jose import jwt as pyjwt

from app.config.settings import Settings
from app.core.security import SecurityManager


# ════════════════════════════════════════════════════════════
# 夹具
# ════════════════════════════════════════════════════════════


@pytest.fixture
def security() -> SecurityManager:
    """使用测试用的密钥构造 SecurityManager"""
    settings = Settings(JWT_SECRET_KEY="test-secret", JWT_ALGORITHM="HS256")
    return SecurityManager(settings)


# ════════════════════════════════════════════════════════════
# 密码哈希与验证
# ════════════════════════════════════════════════════════════


class TestPasswordHashing:
    """测试密码哈希与验证的往返逻辑"""

    def test_hash_and_verify_success(self, security: SecurityManager):
        """正确密码应通过验证"""
        password = "my-strong-password-123!"
        hashed = security.hash_password(password)
        assert security.verify_password(password, hashed)

    def test_wrong_password_fails(self, security: SecurityManager):
        """错误密码应验证失败"""
        hashed = security.hash_password("correct-password")
        assert not security.verify_password("wrong-password", hashed)

    def test_hash_uses_bcrypt(self, security: SecurityManager):
        """哈希结果应以 bcrypt 的 $2b$ 前缀开头"""
        hashed = security.hash_password("any-password")
        assert hashed.startswith("$2b$")

    def test_same_password_different_hashes(self, security: SecurityManager):
        """相同密码每次哈希应不同（salt 随机）"""
        pwd = "same-password"
        h1 = security.hash_password(pwd)
        h2 = security.hash_password(pwd)
        assert h1 != h2
        # 但两者都应能验证
        assert security.verify_password(pwd, h1)
        assert security.verify_password(pwd, h2)

    def test_empty_password(self, security: SecurityManager):
        """空密码也应能正常哈希和验证"""
        hashed = security.hash_password("")
        assert security.verify_password("", hashed)
        assert not security.verify_password("x", hashed)

    def test_unicode_password(self, security: SecurityManager):
        """中文字符等 Unicode 密码应正常工作"""
        pwd = "密码安全测试!@#$%^&*()"
        hashed = security.hash_password(pwd)
        assert security.verify_password(pwd, hashed)
        assert not security.verify_password("密码安全", hashed)


# ════════════════════════════════════════════════════════════
# JWT 令牌创建与验证
# ════════════════════════════════════════════════════════════


class TestTokenCreation:
    """测试 JWT 令牌创建"""

    def test_create_token_returns_string(self, security: SecurityManager):
        """create_access_token 应返回字符串格式的 JWT"""
        token = security.create_access_token(user_id="u1", role="admin")
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT 应包含两到三个点分隔的段
        assert token.count(".") == 2

    def test_token_contains_sub(self, security: SecurityManager):
        """Token payload 应包含 sub (用户 ID)"""
        token = security.create_access_token(user_id="user_abc", role="viewer")
        payload = security.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user_abc"

    def test_token_contains_role(self, security: SecurityManager):
        """Token payload 应包含 role 信息"""
        token = security.create_access_token(user_id="u1", role="admin")
        payload = security.verify_token(token)
        assert payload is not None
        assert payload["role"] == "admin"

    def test_different_users_return_different_sub(self, security: SecurityManager):
        """不同用户的 Token 应包含不同的 user_id"""
        token1 = security.create_access_token(user_id="user_a", role="admin")
        token2 = security.create_access_token(user_id="user_b", role="admin")

        payload1 = security.verify_token(token1)
        payload2 = security.verify_token(token2)
        assert payload1 is not None
        assert payload2 is not None
        assert payload1["sub"] == "user_a"
        assert payload2["sub"] == "user_b"

    def test_token_contains_iat(self, security: SecurityManager):
        """Token payload 应包含签发时间 iat"""
        token = security.create_access_token(user_id="u1", role="admin")
        payload = security.verify_token(token)
        assert payload is not None
        assert "iat" in payload

    def test_token_contains_exp(self, security: SecurityManager):
        """Token payload 应包含过期时间 exp"""
        token = security.create_access_token(user_id="u1", role="admin")
        payload = security.verify_token(token)
        assert payload is not None
        assert "exp" in payload

    def test_token_exp_is_future(self, security: SecurityManager):
        """过期时间应在将来"""
        token = security.create_access_token(user_id="u1", role="admin")
        payload = security.verify_token(token)
        assert payload is not None
        exp = payload["exp"]
        now_ts = datetime.now(timezone.utc).timestamp()
        assert exp > now_ts

    def test_different_roles(self, security: SecurityManager):
        """不同角色的 Token 应包含对应的 role"""
        admin_token = security.create_access_token(user_id="u1", role="admin")
        user_token = security.create_access_token(user_id="u2", role="user")

        admin_payload = security.verify_token(admin_token)
        user_payload = security.verify_token(user_token)
        assert admin_payload is not None
        assert user_payload is not None
        assert admin_payload["role"] == "admin"
        assert user_payload["role"] == "user"


# ════════════════════════════════════════════════════════════
# JWT 异常场景
# ════════════════════════════════════════════════════════════


class TestTokenInvalidScenarios:
    """测试 Token 异常场景（过期、无效签名、非法 token）"""

    def test_expired_token_returns_none(self, security: SecurityManager):
        """过期 Token 应返回 None（优雅降级，不抛异常）"""
        # 手动构造一个已过期的 token
        settings = Settings(JWT_SECRET_KEY="test-secret", JWT_ALGORITHM="HS256")
        payload = {
            "sub": "u1",
            "role": "admin",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        expired_token = pyjwt.encode(payload, "test-secret", algorithm="HS256")
        assert security.verify_token(expired_token) is None

    def test_invalid_signature_returns_none(self, security: SecurityManager):
        """使用不同密钥签名的 Token 应返回 None"""
        # 用 "wrong-secret" 签名，用 "test-secret" 验证
        settings = Settings(JWT_SECRET_KEY="wrong-secret", JWT_ALGORITHM="HS256")
        bad_security = SecurityManager(settings)
        token = bad_security.create_access_token(user_id="u1", role="admin")
        assert security.verify_token(token) is None

    def test_malformed_token_returns_none(self, security: SecurityManager):
        """非法的 token 字符串应返回 None"""
        assert security.verify_token("") is None
        assert security.verify_token("not-a-jwt") is None
        assert security.verify_token("invalid.with.dots") is None

    def test_tampered_token_returns_none(self, security: SecurityManager):
        """被篡改的 token 应返回 None"""
        token = security.create_access_token(user_id="u1", role="admin")
        # 翻转最后一个字符
        tampered = token[:-1] + ("X" if token[-1] != "X" else "Y")
        assert security.verify_token(tampered) is None

    def test_none_token_returns_none(self, security: SecurityManager):
        """传入 None 应优雅处理（TypeError 被捕获）"""
        # 类型忽略，模拟接口意外传 None
        assert security.verify_token(None) is None  # type: ignore

    def test_empty_user_id(self, security: SecurityManager):
        """空字符串 user_id 应能正常创建和验证"""
        token = security.create_access_token(user_id="", role="admin")
        payload = security.verify_token(token)
        assert payload is not None
        assert payload["sub"] == ""

    def test_empty_role(self, security: SecurityManager):
        """空字符串 role 应能正常创建和验证"""
        token = security.create_access_token(user_id="u1", role="")
        payload = security.verify_token(token)
        assert payload is not None
        assert payload["role"] == ""


# ════════════════════════════════════════════════════════════
# 跨场景完整性
# ════════════════════════════════════════════════════════════


class TestSecurityIntegration:
    """安全模块的集成功能测试"""

    def test_password_and_token_independent(self, security: SecurityManager):
        """密码和 Token 功能互不干扰"""
        hashed = security.hash_password("secret-pass")
        assert security.verify_password("secret-pass", hashed)

        token = security.create_access_token(
            user_id="integration_user", role="editor"
        )
        payload = security.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "integration_user"
        assert payload["role"] == "editor"

    def test_long_password(self, security: SecurityManager):
        """长密码应正常处理（bcrypt 72 字节截断特性）"""
        long_pwd = "a" * 100  # bcrypt 只使用前 72 字节
        hashed = security.hash_password(long_pwd)
        assert security.verify_password(long_pwd, hashed)
        # bcrypt 截断后，"a"*72 和 "a"*100 前 72 字节相同
        assert security.verify_password("a" * 72, hashed)
