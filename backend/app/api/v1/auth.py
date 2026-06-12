"""认证路由 — 注册、登录、Token 刷新

/auth/*
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import Container, get_container
from app.schemas.common import ApiResponse
from app.schemas.user import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.services.user_service import (
    UserAlreadyExists,
    UserInactive,
    UserService,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    container: Container = Depends(get_container),
):
    """用户注册

    创建新用户账户。用户名必须唯一且为字母数字下划线组合。
    """
    if container.user_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户服务未初始化",
        )

    try:
        user = await container.user_service.register(request)
        return ApiResponse(code=201, message="注册成功", data=user.model_dump())
    except UserAlreadyExists as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.post("/login", response_model=ApiResponse)
async def login(
    request: UserLoginRequest,
    container: Container = Depends(get_container),
):
    """用户登录

    验证用户名和密码，返回 JWT 令牌和用户信息。
    """
    if container.user_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户服务未初始化",
        )

    try:
        token = await container.user_service.login(request)
        return ApiResponse(
            code=200,
            message="登录成功",
            data=token.model_dump(),
        )
    except UserInactive as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )
    except Exception as e:
        from app.services.user_service import InvalidCredentials

        if isinstance(e, InvalidCredentials):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=e.message,
            )
        raise


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(
    container: Container = Depends(get_container),
):
    """刷新 Token（预留）

    目前返回当前用户的新令牌。需要进一步完善。
    """
    # 预留实现 — 后续可扩展为使用 refresh_token
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token 刷新功能尚未实现",
    )
