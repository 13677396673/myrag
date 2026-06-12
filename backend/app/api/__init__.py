"""API 路由模块 — HTTP 接口层

提供面向客户端的 RESTful API，包含认证、用户、数据集、
文档、对话、管理后台等所有端点。
"""

from .deps import Container, get_container, get_current_user_id, require_admin
from .errors import register_exception_handlers

__all__ = [
    "Container",
    "get_container",
    "get_current_user_id",
    "require_admin",
    "register_exception_handlers",
]
