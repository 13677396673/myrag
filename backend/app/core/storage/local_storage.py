"""本地文件存储实现 — LocalFileStorage

将文件保存到本地文件系统，支持自动创建中间目录。

用法::

    storage = LocalFileStorage(base_path="./data/uploads")
    path = await storage.save("user_1/doc.pdf", pdf_bytes)
    data = await storage.read("user_1/doc.pdf")
"""

import os
from pathlib import Path
from typing import Optional

from app.core.exceptions import StorageError
from app.core.storage.base import FileStorageBackend


class LocalFileStorage(FileStorageBackend):
    """本地文件系统存储后端

    属性:
        base_path: 存储根目录的绝对路径
    """

    def __init__(self, base_path: str) -> None:
        """初始化本地存储

        参数:
            base_path: 存储根目录；如果不存在则自动创建

        异常:
            StorageError: 根目录创建失败时抛出
        """
        self._base_path = Path(base_path).resolve()
        try:
            self._base_path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(
                message=f"无法创建存储根目录: {self._base_path}",
                detail=str(exc),
            ) from exc

    @property
    def base_path(self) -> str:
        """存储根目录的字符串形式"""
        return str(self._base_path)

    # ── 私有辅助 ──────────────────────────────────────────────

    def _resolve(self, storage_path: str) -> Path:
        """将 ``storage_path`` 解析为绝对路径，并做路径穿越防护"""
        # 防止 path traversal：解析后的路径必须在 base_path 下
        resolved = (self._base_path / storage_path).resolve()
        if not str(resolved).startswith(str(self._base_path) + os.sep) and resolved != self._base_path:
            raise StorageError(
                message="路径穿越攻击被拒绝",
                detail=f"storage_path={storage_path!r} 解析到了 base_path 之外",
            )
        return resolved

    # ── 接口实现 ──────────────────────────────────────────────

    async def save(self, storage_path: str, content: bytes) -> str:
        """保存文件 — 自动创建中间目录，以二进制形式写入

        返回:
            实际写入的绝对路径

        异常:
            StorageError: 写入失败（权限不足、磁盘满等）
        """
        target = self._resolve(storage_path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            return str(target)
        except OSError as exc:
            raise StorageError(
                message=f"文件写入失败: {storage_path}",
                detail=str(exc),
            ) from exc

    async def read(self, storage_path: str) -> Optional[bytes]:
        """读取文件内容

        返回:
            - 文件存在 → bytes
            - 不存在    → None
        """
        target = self._resolve(storage_path)
        try:
            return target.read_bytes()
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise StorageError(
                message=f"文件读取失败: {storage_path}",
                detail=str(exc),
            ) from exc

    async def delete(self, storage_path: str) -> bool:
        """删除文件

        返回:
            - 原本存在并被删除 → ``True``
            - 原本就不存在     → ``False``
        """
        target = self._resolve(storage_path)
        try:
            target.unlink(missing_ok=False)
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise StorageError(
                message=f"文件删除失败: {storage_path}",
                detail=str(exc),
            ) from exc

    async def exists(self, storage_path: str) -> bool:
        """检查文件是否存在（仅检查文件，忽略目录）"""
        target = self._resolve(storage_path)
        return target.is_file()
