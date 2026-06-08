"""用户相关 Pydantic 模式 — 注册、登录、信息响应、密码修改"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


class UserRegisterRequest(BaseModel):
    """用户注册请求"""

    username: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="用户名，2~50 位字母数字下划线",
    )
    email: EmailStr = Field(..., description="电子邮箱")
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="密码，6~128 位",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """用户名只能包含字母、数字、下划线"""
        if not USERNAME_PATTERN.match(v):
            raise ValueError(
                "用户名只能包含字母、数字和下划线"
            )
        return v


class UserLoginRequest(BaseModel):
    """用户登录请求"""

    username: str = Field(
        ..., min_length=1, description="用户名"
    )
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户信息响应"""

    id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="电子邮箱")
    role: str = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""

    email: Optional[EmailStr] = Field(None, description="新电子邮箱")


class PasswordChangeRequest(BaseModel):
    """修改密码请求"""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="新密码，6~128 位",
    )


class TokenResponse(BaseModel):
    """登录令牌响应"""

    access_token: str = Field(..., description="JWT 令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: UserResponse = Field(..., description="用户信息")
