"""数据集相关 Pydantic 模式"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DatasetCreateRequest(BaseModel):
    """创建数据集请求"""

    name: str = Field(
        ..., min_length=1, max_length=255, description="数据集名称"
    )
    description: Optional[str] = Field(None, description="数据集描述")


class DatasetUpdateRequest(BaseModel):
    """更新数据集请求"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="数据集名称"
    )
    description: Optional[str] = Field(None, description="数据集描述")


class DatasetResponse(BaseModel):
    """数据集信息响应"""

    id: str = Field(..., description="数据集 ID")
    name: str = Field(..., description="数据集名称")
    description: Optional[str] = Field(None, description="数据集描述")
    document_count: int = Field(default=0, description="文档数量")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = {"from_attributes": True}
