"""用户路由 — 个人信息管理

/users/me/*
"""

from fastapi import APIRouter, Depends

from app.api.deps import Container, get_container, get_current_user_id
from app.schemas.common import ApiResponse
from app.schemas.user import PasswordChangeRequest, UserUpdateRequest
from app.services.user_service import (
    PasswordNotMatch,
    UserAlreadyExists,
    UserNotFound,
)

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", response_model=ApiResponse)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """获取当前用户信息"""
    user = await container.user_service.get_user_by_id(user_id)
    return ApiResponse(code=200, message="success", data=user.model_dump())


@router.put("/me", response_model=ApiResponse)
async def update_current_user(
    request: UserUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """更新个人信息（邮箱）"""
    try:
        user = await container.user_service.update_user(user_id, request)
        return ApiResponse(
            code=200, message="更新成功", data=user.model_dump()
        )
    except UserAlreadyExists as e:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        )
    except UserNotFound as e:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )


@router.put("/me/password", response_model=ApiResponse)
async def change_password(
    request: PasswordChangeRequest,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """修改当前用户密码"""
    try:
        await container.user_service.change_password(user_id, request)
        return ApiResponse(code=200, message="密码修改成功")
    except PasswordNotMatch as e:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        )
    except UserNotFound as e:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )
