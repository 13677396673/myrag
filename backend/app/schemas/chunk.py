"""文档切片 Pydantic 模式"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ChunkResponse(BaseModel):
    """切片信息响应"""

    id: str = Field(..., description="切片 ID")
    document_id: str = Field(..., description="所属文档 ID")
    content: str = Field(..., description="切片内容")
    chunk_index: int = Field(..., description="切片序号")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

    model_config = {"from_attributes": True}
