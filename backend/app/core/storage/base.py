"""文件存储抽象接口 — FileStorageBackend

定义文件存储后端的统一抽象，所有具体实现（本地文件、S3、MinIO）必须
继承此基类并实现所有方法。

用法::

    class MyStorage(FileStorageBackend):
        async def save(self, storage_path: str, content: bytes) -> str: ...
        async def read(self, storage_path: str) -> Optional[bytes]: ...
        async def delete(self, storage_path: str) -> bool: ...
        async def exists(self, storage_path: str) -> bool: ...
"""

from abc import ABC, abstractmethod
from typing import Optional


class FileStorageBackend(ABC):
    """文件存储后端抽象接口

    所有方法均为 ``async``，支持替换为 S3 / MinIO / 其他远程存储实现。

    ``storage_path`` 是存储端的相对路径，由调用方生成（例如
    ``user_id/document_id/filename``），具体实现负责将其映射为实际
    存储路径。
    """

    @abstractmethod
    async def save(self, storage_path: str, content: bytes) -> str:
        """保存文件内容

        参数:
            storage_path: 存储相对路径（如 ``alice/report.pdf``）
            content:      文件二进制内容

        返回:
            实际写入的完整路径字符串

        异常:
            StorageError: 写入失败时抛出
        """
        ...

    @abstractmethod
    async def read(self, storage_path: str) -> Optional[bytes]:
        """读取文件内容

        参数:
            storage_path: 存储相对路径

        返回:
            - 文件存在 → 文件 bytes
            - 不存在    → ``None``（不抛出异常）
        """
        ...

    @abstractmethod
    async def delete(self, storage_path: str) -> bool:
        """删除文件

        参数:
            storage_path: 存储相对路径

        返回:
            - 原本存在并被删除 → ``True``
            - 原本就不存在     → ``False``
        """
        ...

    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """检查文件是否存在

        参数:
            storage_path: 存储相对路径

        返回:
            ``True`` 如果文件存在，否则 ``False``
        """
        ...
