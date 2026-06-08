"""安全模块 — SecurityManager

提供密码哈希验证（bcrypt）和 JWT 令牌创建/验证（python-jose）功能。
所有方法均为同步方法，方便在 FastAPI 依赖注入中调用。
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config.settings import Settings


class SecurityManager:
    """安全管理器：密码哈希 + JWT 令牌

    用法::

        security = SecurityManager(settings)
        hashed = security.hash_password("my-pass")
        assert security.verify_password("my-pass", hashed)

        token = security.create_access_token(user_id="u1", role="admin")
        payload = security.verify_token(token)
        assert payload["sub"] == "u1"
    """

    def __init__(self, settings: Settings) -> None:
        """保存配置引用"""
        self._settings = settings

    # ── 密码哈希 ──────────────────────────────────────────────

    def hash_password(self, password: str) -> str:
        """使用 bcrypt 对明文密码进行哈希，返回字符串格式的哈希值

        注意：bcrypt 内部仅使用前 72 字节，此处显式截断以兼容
        bcrypt>=4.1 的严格检查。
        """
        pwd_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        """验证明文密码是否与 bcrypt 哈希匹配

        注意：bcrypt 内部仅使用前 72 字节，此处与 ``hash_password``
        保持一致进行截断。
        """
        plain_bytes = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)

    # ── JWT 令牌 ──────────────────────────────────────────────

    def create_access_token(self, user_id: str, role: str) -> str:
        """创建 JWT access token

        Payload 包含：
        - ``sub``: 用户 ID
        - ``role``: 用户角色
        - ``exp``: 过期时间（UTC）
        - ``iat``: 签发时间（UTC）

        签名算法、密钥、过期时间均从 ``Settings`` 读取。
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(
            minutes=self._settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

        payload = {
            "sub": user_id,
            "role": role,
            "iat": now,
            "exp": expire,
        }
        return jwt.encode(
            payload,
            self._settings.JWT_SECRET_KEY,
            algorithm=self._settings.JWT_ALGORITHM,
        )

    def verify_token(self, token: str) -> Optional[dict]:
        """验证 JWT token 并解码 payload

        返回:
            - 有效 token → payload 字典（含 ``sub``, ``role``, ``exp``, ``iat``）
            - 过期 token → ``None``
            - 签名无效 → ``None``
            - 其他异常  → ``None``
        """
        if not token:
            return None
        try:
            payload = jwt.decode(
                token,
                self._settings.JWT_SECRET_KEY,
                algorithms=[self._settings.JWT_ALGORITHM],
            )
            return payload
        except JWTError:
            return None
