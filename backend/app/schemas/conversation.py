"""对话与消息相关 Pydantic 模式"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    """创建对话请求"""

    title: str = Field(
        default="新对话", max_length=255, description="对话标题"
    )
    dataset_id: Optional[str] = Field(None, description="关联数据集 ID")


class ConversationResponse(BaseModel):
    """对话信息响应"""

    id: str = Field(..., description="对话 ID")
    title: str = Field(..., description="对话标题")
    dataset_id: Optional[str] = Field(None, description="关联数据集 ID")
    message_count: int = Field(default=0, description="消息数量")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = {"from_attributes": True}


class MessageSendRequest(BaseModel):
    """发送消息请求"""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="消息内容，1~10000 字符",
    )


class SourceCitation(BaseModel):
    """来源引用"""

    chunk_id: str = Field(..., description="切片 ID")
    content: str = Field(..., description="引用内容片段")
    document_name: str = Field(..., description="来源文档名称")
    score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="相关性分数"
    )


class MessageResponse(BaseModel):
    """消息响应"""

    id: str = Field(..., description="消息 ID")
    role: str = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    sources: List[SourceCitation] = Field(
        default_factory=list, description="引用来源"
    )
    created_at: Optional[datetime] = Field(None, description="创建时间")

    model_config = {"from_attributes": True}


class MessageStreamDelta(BaseModel):
    """SSE 流式增量事件"""

    type: str = Field(default="delta", description="事件类型")
    content: str = Field(..., description="增量内容")


class MessageStreamDone(BaseModel):
    """SSE 流式完成事件"""

    type: str = Field(default="done", description="事件类型")
    message_id: str = Field(..., description="完成后的消息 ID")


class MessageStreamSources(BaseModel):
    """SSE 流式来源事件"""

    type: str = Field(default="sources", description="事件类型")
    sources: List[SourceCitation] = Field(
        ..., description="引用来源列表"
    )


class MessageStreamError(BaseModel):
    """SSE 流式错误事件"""

    type: str = Field(default="error", description="事件类型")
    content: str = Field(..., description="错误信息")


# SSE 事件联合类型
MessageStreamEvent = Annotated[
    Union[
        MessageStreamDelta,
        MessageStreamDone,
        MessageStreamSources,
        MessageStreamError,
    ],
    Field(discriminator="type"),
]
