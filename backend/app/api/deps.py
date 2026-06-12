"""API 依赖注入 — JWT 鉴权、DI 容器、当前用户获取

提供 FastAPI 依赖注入函数，用于：
- JWT token 验证与当前用户解析
- 管理员权限检查
- 全局服务容器管理

API 层统一通过 ``app.core.container.Container`` 访问所有服务和组件。
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.container import Container

# 无 token 时返回 None 而非 403（由依赖函数自行处理）
bearer_scheme = HTTPBearer(auto_error=False)


# ════════════════════════════════════════════════════════════
# DI 容器获取
# ════════════════════════════════════════════════════════════


async def get_container() -> Container:
    """FastAPI 依赖：返回全局 DI 容器

    通过 ``Container.get()`` 获取全局单例；测试可通过
    ``app.dependency_overrides[get_container]`` 覆盖。
    """
    return await Container.get()


def set_container(container: Container) -> None:
    """设置全局容器（供 main.py 使用）"""
    Container.set_container(container)


# ════════════════════════════════════════════════════════════
# 鉴权依赖
# ════════════════════════════════════════════════════════════


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    container: Container = Depends(get_container),
) -> str:
    """从 JWT token 中解析当前用户 ID

    流程:
        1. 检查 Bearer token 是否存在
        2. 用 SecurityManager 验证 token 签名和有效期
        3. 从 payload 中提取 ``sub``（用户 ID）

    异常:
        HTTPException(401) — token 缺失、无效、过期
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = container.security.verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub", "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def require_admin(
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
) -> str:
    """要求当前用户为管理员

    通过 UserService 查询用户角色，若非 admin 则拒绝。

    异常:
        HTTPException(403) — 非管理员用户
    """
    user = await container.user_service.get_user_by_id(user_id)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    return user_id
