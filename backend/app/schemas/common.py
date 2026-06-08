"""通用 Pydantic 模式 — 统一响应包装、分页参数"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    """统一 API 响应包装

    所有 API 响应均使用此结构，前端通过 code 判断业务成功与否。
    """

    code: int = Field(default=200, description="业务状态码")
    message: str = Field(default="success", description="提示信息")
    data: Optional[DataT] = Field(default=None, description="响应数据")


class PaginationParams(BaseModel):
    """分页请求参数"""

    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(
        default=20, ge=1, le=100, description="每页条数，最大 100"
    )


class PaginatedResponse(BaseModel, Generic[DataT]):
    """分页响应"""

    items: List[DataT] = Field(default=[], description="当前页数据列表")
    total: int = Field(default=0, ge=0, description="总记录数")
    page: int = Field(default=1, ge=1, description="当前页码")
    page_size: int = Field(default=20, ge=1, description="每页条数")
    total_pages: int = Field(default=0, ge=0, description="总页数")

    @classmethod
    def build(
        cls,
        items: List[DataT],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[DataT]":
        """便捷构造分页响应"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
