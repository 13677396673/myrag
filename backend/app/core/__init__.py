"""核心基础模块

提供数据库管理、全局异常等基础能力。
"""

from .database import DatabaseManager
from .exceptions import RagError, ConfigError, StorageError

__all__ = [
    "DatabaseManager",
    "RagError",
    "ConfigError",
    "StorageError",
]
