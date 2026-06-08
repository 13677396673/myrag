"""本地文件存储 LocalFileStorage 测试"""

import os
from pathlib import Path

import pytest

from app.core.exceptions import StorageError
from app.core.storage import LocalFileStorage


class TestLocalFileStorage:
    """LocalFileStorage 功能测试"""

    # ── 保存与读取 ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_save_and_read(self, local_storage: LocalFileStorage) -> None:
        """保存文件后，读取内容一致"""
        path = "hello.txt"
        content = b"Hello, World!"
        saved = await local_storage.save(path, content)
        assert isinstance(saved, str)
        assert Path(saved).is_file()

        read_back = await local_storage.read(path)
        assert read_back == content

    @pytest.mark.asyncio
    async def test_read_nonexistent_returns_none(self, local_storage: LocalFileStorage) -> None:
        """读取不存在的文件返回 None（不抛异常）"""
        result = await local_storage.read("nonexistent/file.txt")
        assert result is None

    # ── 删除 ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, local_storage: LocalFileStorage) -> None:
        """删除存在的文件返回 True"""
        await local_storage.save("delete_me.txt", b"bye")
        result = await local_storage.delete("delete_me.txt")
        assert result is True
        assert await local_storage.exists("delete_me.txt") is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, local_storage: LocalFileStorage) -> None:
        """删除不存在的文件返回 False"""
        result = await local_storage.delete("i_do_not_exist.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_twice(self, local_storage: LocalFileStorage) -> None:
        """重复删除已删除的文件，第二次返回 False"""
        await local_storage.save("twice.txt", b"data")
        assert await local_storage.delete("twice.txt") is True
        assert await local_storage.delete("twice.txt") is False

    # ── 存在性检查 ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_exists_after_save(self, local_storage: LocalFileStorage) -> None:
        """保存后 exists 返回 True"""
        await local_storage.save("exists_check.txt", b"data")
        assert await local_storage.exists("exists_check.txt") is True

    @pytest.mark.asyncio
    async def test_exists_after_delete(self, local_storage: LocalFileStorage) -> None:
        """删除后 exists 返回 False"""
        await local_storage.save("gone_soon.txt", b"data")
        await local_storage.delete("gone_soon.txt")
        assert await local_storage.exists("gone_soon.txt") is False

    @pytest.mark.asyncio
    async def test_exists_nonexistent(self, local_storage: LocalFileStorage) -> None:
        """不存在的文件返回 False"""
        assert await local_storage.exists("nothing.txt") is False

    @pytest.mark.asyncio
    async def test_exists_on_directory_returns_false(self, local_storage: LocalFileStorage) -> None:
        """对目录路径执行 exists 返回 False（仅检测文件）"""
        # 先保存一个文件，使其父目录被创建
        await local_storage.save("subdir/keep.txt", b"x")
        # 目录路径本身不应被视为文件
        assert await local_storage.exists("subdir") is False

    # ── 嵌套子目录 ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_save_nested_directory(self, local_storage: LocalFileStorage) -> None:
        """保存到嵌套子目录时自动创建中间目录"""
        content = b"nested content"
        path = "a/b/c/d/deep_file.txt"
        saved = await local_storage.save(path, content)
        assert Path(saved).is_file()

        read_back = await local_storage.read(path)
        assert read_back == content

    @pytest.mark.asyncio
    async def test_save_nested_directory_deep(self, local_storage: LocalFileStorage) -> None:
        """深层嵌套（10层）子目录自动创建"""
        content = b"deep"
        path = "/".join([f"lvl{i}" for i in range(10)]) + "/deep.txt"
        saved = await local_storage.save(path, content)
        assert Path(saved).is_file()
        assert await local_storage.read(path) == content

    # ── 二进制内容 ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_binary_content_pdf(self, local_storage: LocalFileStorage) -> None:
        """保存和读取二进制内容（模拟 PDF）"""
        # PDF 文件头：%PDF-1.4
        pdf_header = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        path = "documents/sample.pdf"
        await local_storage.save(path, pdf_header)
        assert await local_storage.read(path) == pdf_header

    @pytest.mark.asyncio
    async def test_binary_content_image(self, local_storage: LocalFileStorage) -> None:
        """保存和读取二进制内容（模拟图片）"""
        # 模拟一张小 PNG（8 字节无效但可测试二进制完整性）
        png_data = bytes(range(256))  # 全字节集 0x00-0xFF
        path = "images/test.png"
        await local_storage.save(path, png_data)
        assert await local_storage.read(path) == png_data

    @pytest.mark.asyncio
    async def test_binary_content_null_bytes(self, local_storage: LocalFileStorage) -> None:
        """保存和读取包含 \\0 的二进制内容"""
        data = b"\x00\x01\x02\x00\xff\xfe\x00"
        path = "binary/null_test.bin"
        await local_storage.save(path, data)
        assert await local_storage.read(path) == data

    @pytest.mark.asyncio
    async def test_empty_file(self, local_storage: LocalFileStorage) -> None:
        """保存空文件也能正常读写"""
        path = "empty.txt"
        await local_storage.save(path, b"")
        assert await local_storage.read(path) == b""

    # ── 大文件 ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_large_file(self, local_storage: LocalFileStorage) -> None:
        """接近 max_file_size（50MB）的大文件读写正常"""
        # 用 5MB 替代 50MB 以加速测试，但逻辑一致
        size = 5 * 1024 * 1024
        content = b"X" * size
        path = "large/large_file.bin"
        saved = await local_storage.save(path, content)
        assert Path(saved).is_file()
        assert Path(saved).stat().st_size == size

        read_back = await local_storage.read(path)
        assert read_back == content
        assert len(read_back) == size

    # ── 路径穿越防护 ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, local_storage: LocalFileStorage) -> None:
        """试图通过 ../ 跳出存储根目录应当抛出 StorageError"""
        with pytest.raises(StorageError, match="路径穿越攻击被拒绝"):
            await local_storage.save("../../etc/passwd", b"evil")

    @pytest.mark.asyncio
    async def test_path_traversal_read(self, local_storage: LocalFileStorage) -> None:
        """读取路径穿越路径应抛出 StorageError"""
        with pytest.raises(StorageError, match="路径穿越攻击被拒绝"):
            await local_storage.read("../../../windows/win.ini")

    # ── base_path 初始化 ────────────────────────────────────

    def test_base_path_created_if_not_exists(self) -> None:
        """如果 base_path 目录不存在，初始化时自动创建"""
        import tempfile
        tmp = tempfile.mkdtemp()
        base = os.path.join(tmp, "new_dir", "sub")
        storage = LocalFileStorage(base)
        assert os.path.isdir(base)
        assert storage.base_path == os.path.abspath(base)

    def test_base_path_property(self, local_storage: LocalFileStorage, tmp_dir: str) -> None:
        """base_path 属性返回正确的绝对路径"""
        expected = os.path.abspath(tmp_dir)
        assert local_storage.base_path == expected
