"""管理后台 Pydantic 模式"""

from pydantic import BaseModel, Field


class SystemStatsResponse(BaseModel):
    """系统统计信息响应"""

    total_users: int = Field(default=0, ge=0, description="用户总数")
    total_documents: int = Field(
        default=0, ge=0, description="文档总数"
    )
    total_conversations: int = Field(
        default=0, ge=0, description="对话总数"
    )
    total_chunks: int = Field(default=0, ge=0, description="切片总数")
    active_users_today: int = Field(
        default=0, ge=0, description="今日活跃用户数"
    )
