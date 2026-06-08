"""文件存储模块

提供统一的 ``FileStorageBackend`` 抽象接口及本地文件系统实现
``LocalFileStorage``，支持未来替换为 S3 / MinIO 等远程存储后端。
"""

from .base import FileStorageBackend
from .local_storage import LocalFileStorage

__all__ = [
    "FileStorageBackend",
    "LocalFileStorage",
]
