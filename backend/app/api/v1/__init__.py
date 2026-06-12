"""API v1 路由注册

聚合所有子路由模块，挂载到 ``/api/v1`` 前缀下。
"""

from fastapi import APIRouter

from .admin import router as admin_router
from .auth import router as auth_router
from .conversations import router as conversations_router
from .datasets import router as datasets_router
from .documents import router as documents_router
from .users import router as users_router

# 主路由器：所有 v1 接口统一前缀
v1_router = APIRouter(prefix="/api/v1")

# 注册子路由
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(datasets_router)
v1_router.include_router(documents_router)
v1_router.include_router(conversations_router)
v1_router.include_router(admin_router)


__all__ = ["v1_router"]
