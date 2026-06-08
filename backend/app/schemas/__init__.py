"""Pydantic 模式模块 — 所有 API 请求/响应定义"""

from .admin import SystemStatsResponse
from .chunk import ChunkResponse
from .common import ApiResponse, PaginatedResponse, PaginationParams
from .conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageResponse,
    MessageSendRequest,
    MessageStreamDelta,
    MessageStreamDone,
    MessageStreamError,
    MessageStreamEvent,
    MessageStreamSources,
    SourceCitation,
)
from .dataset import (
    DatasetCreateRequest,
    DatasetResponse,
    DatasetUpdateRequest,
)
from .document import DocumentResponse, DocumentStatusResponse
from .user import (
    PasswordChangeRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)

__all__ = [
    # Common
    "ApiResponse",
    "PaginatedResponse",
    "PaginationParams",
    # User
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "UserUpdateRequest",
    "PasswordChangeRequest",
    "TokenResponse",
    # Dataset
    "DatasetCreateRequest",
    "DatasetUpdateRequest",
    "DatasetResponse",
    # Document
    "DocumentResponse",
    "DocumentStatusResponse",
    # Chunk
    "ChunkResponse",
    # Conversation
    "ConversationCreateRequest",
    "ConversationResponse",
    "MessageSendRequest",
    "SourceCitation",
    "MessageResponse",
    "MessageStreamDelta",
    "MessageStreamDone",
    "MessageStreamSources",
    "MessageStreamError",
    "MessageStreamEvent",
    # Admin
    "SystemStatsResponse",
]
