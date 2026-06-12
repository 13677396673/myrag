"""管理后台路由 — 用户管理、系统统计

/admin/*
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    Container,
    get_container,
    require_admin,
)
from app.schemas.common import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/admin", tags=["管理后台"])


@router.get("/users", response_model=ApiResponse)
async def list_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    _admin_id: str = Depends(require_admin),
    container: Container = Depends(get_container),
):
    """获取用户列表（需要管理员权限）"""
    result = await container.admin_service.list_users(
        page=page,
        page_size=page_size,
    )
    paginated = PaginatedResponse.build(
        items=[user.model_dump() for user in result["users"]],
        total=result["total"],
        page=page,
        page_size=page_size,
    )
    return ApiResponse(
        code=200, message="success", data=paginated.model_dump()
    )


@router.get("/stats", response_model=ApiResponse)
async def get_stats(
    _admin_id: str = Depends(require_admin),
    container: Container = Depends(get_container),
):
    """获取系统统计信息（需要管理员权限）

    包含用户总数、文档总数、对话总数、切片总数、今日活跃用户数。
    """
    stats = await container.admin_service.get_stats()
    return ApiResponse(
        code=200, message="success", data=stats.model_dump()
    )
