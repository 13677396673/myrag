"""业务服务模块 — 所有业务逻辑封装在此层"""

from .conversation_service import (
    ConversationNotFound,
    ConversationService,
    ConversationServiceError,
)
from .dataset_service import (
    DatasetNotFound,
    DatasetPermissionDenied,
    DatasetService,
    DatasetServiceError,
)
from .document_service import (
    DocumentNotFound,
    DocumentPermissionDenied,
    DocumentService,
    DocumentServiceError,
    UnsupportedFileType,
)
from .user_service import (
    UserAlreadyExists,
    UserInactive,
    UserNotFound,
    UserService,
    UserServiceError,
)

__all__ = [
    # User
    "UserService",
    "UserServiceError",
    "UserAlreadyExists",
    "UserNotFound",
    "UserInactive",
    # Dataset
    "DatasetService",
    "DatasetServiceError",
    "DatasetNotFound",
    "DatasetPermissionDenied",
    # Document
    "DocumentService",
    "DocumentServiceError",
    "DocumentNotFound",
    "DocumentPermissionDenied",
    "UnsupportedFileType",
    # Conversation
    "ConversationService",
    "ConversationServiceError",
    "ConversationNotFound",
]
