"""文档相关 Pydantic 模式"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """文档信息响应"""

    id: str = Field(..., description="文档 ID")
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    status: str = Field(..., description="处理状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    dataset_id: Optional[str] = Field(None, description="所属数据集 ID")
    chunk_count: int = Field(default=0, description="切片数量")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = {"from_attributes": True}


class DocumentStatusResponse(BaseModel):
    """文档处理状态响应"""

    id: str = Field(..., description="文档 ID")
    status: str = Field(..., description="处理状态")
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="处理进度，0~1",
    )
    error_message: Optional[str] = Field(None, description="错误信息")
