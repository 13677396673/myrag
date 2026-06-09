"""
FixedSizeSplitter 单元测试

测试策略：
- 短文本 → 返回 1 个 chunk（无多余切分）
- 长文本 → 返回多个 chunk，验证 overlap 正确
- overlap >= chunk_size → 抛 ValueError
- 空文本 → 返回空列表
- metadata 透传到每个 chunk
- chunk_index 从 0 开始递增
"""

import pytest

from app.rag.splitters import FixedSizeSplitter
from app.rag.interfaces.splitter import DocumentChunk


class TestFixedSizeSplitterInit:
    """初始化参数校验"""

    def test_default_params(self):
        splitter = FixedSizeSplitter()
        assert splitter._chunk_size == 512
        assert splitter._chunk_overlap == 64
        assert splitter.type_name == "fixed"

    def test_custom_params(self):
        splitter = FixedSizeSplitter(chunk_size=256, chunk_overlap=32)
        assert splitter._chunk_size == 256
        assert splitter._chunk_overlap == 32

    def test_overlap_equal_to_chunk_size_raises(self):
        with pytest.raises(ValueError, match="chunk_overlap.*必须小于.*chunk_size"):
            FixedSizeSplitter(chunk_size=100, chunk_overlap=100)

    def test_overlap_greater_than_chunk_size_raises(self):
        with pytest.raises(ValueError, match="chunk_overlap.*必须小于.*chunk_size"):
            FixedSizeSplitter(chunk_size=100, chunk_overlap=200)


class TestFixedSizeSplitterSplit:
    """核心切分逻辑"""

    def test_empty_text_returns_empty_list(self):
        splitter = FixedSizeSplitter()
        assert splitter.split("") == []
        assert splitter.split("", metadata={"doc_id": "1"}) == []

    def test_short_text_returns_one_chunk(self):
        splitter = FixedSizeSplitter(chunk_size=100, chunk_overlap=10)
        text = "Hello world"
        chunks = splitter.split(text)
        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].chunk_index == 0

    def test_text_equal_to_chunk_size_returns_one_chunk(self):
        splitter = FixedSizeSplitter(chunk_size=10, chunk_overlap=2)
        text = "A" * 10
        chunks = splitter.split(text)
        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_long_text_returns_multiple_chunks(self):
        splitter = FixedSizeSplitter(chunk_size=10, chunk_overlap=2)
        text = "A" * 25
        chunks = splitter.split(text)
        assert len(chunks) >= 2

    def test_chunk_index_starts_at_zero_and_increments(self):
        splitter = FixedSizeSplitter(chunk_size=5, chunk_overlap=1)
        text = "A" * 15
        chunks = splitter.split(text)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_metadata_passed_to_all_chunks(self):
        splitter = FixedSizeSplitter(chunk_size=10, chunk_overlap=2)
        text = "A" * 30
        metadata = {"document_id": "doc_123", "user_id": "user_456"}
        chunks = splitter.split(text, metadata=metadata)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.metadata["document_id"] == "doc_123"
            assert chunk.metadata["user_id"] == "user_456"

    def test_metadata_contains_chunk_size_record(self):
        splitter = FixedSizeSplitter(chunk_size=10, chunk_overlap=2)
        text = "A" * 10
        chunks = splitter.split(text, metadata={"doc_id": "1"})
        assert chunks[0].metadata["chunk_size"] == 10
        assert chunks[0].metadata["doc_id"] == "1"

    def test_none_metadata_is_handled(self):
        splitter = FixedSizeSplitter(chunk_size=10, chunk_overlap=2)
        text = "Hello"
        chunks = splitter.split(text, metadata=None)
        assert len(chunks) == 1
        # None metadata 转为空 dict，只包含 chunk_size
        assert "chunk_size" in chunks[0].metadata

    def test_overlap_logic_exact(self):
        splitter = FixedSizeSplitter(chunk_size=10, chunk_overlap=3)
        text = "A" * 25  # 25 chars
        chunks = splitter.split(text)
        # Chunk 0: [0:10],  Chunk 1: [7:17],  Chunk 2: [14:24],  Chunk 3: [21:25]
        assert len(chunks) == 4
        assert chunks[0].content == "A" * 10       # 0-10
        assert chunks[1].content == "A" * 10       # 7-17 (10 chars)
        assert chunks[2].content == "A" * 10       # 14-24 (10 chars)
        assert chunks[3].content == "A" * 4        # 21-25 (4 chars, last)

    def test_no_unnecessary_empty_chunks(self):
        splitter = FixedSizeSplitter(chunk_size=10, chunk_overlap=2)
        text = "A" * 20  # with overlap=2 → 3 chunks, last is short but not empty
        chunks = splitter.split(text)
        assert len(chunks) == 3  # chunk_size=10, overlap=2, len=20: 0-10, 8-18, 16-20
        assert all(c.content for c in chunks)  # no empty content

    def test_chinese_text(self):
        splitter = FixedSizeSplitter(chunk_size=10, chunk_overlap=2)
        text = "你好世界，这是一个测试文本用于验证中文切片"
        chunks = splitter.split(text)
        assert len(chunks) >= 1
        # Verify each chunk's content is non-empty
        assert all(c.content for c in chunks)
        # Verify original text is fully covered by chunks (with overlap)
        all_content = "".join(c.content for c in chunks)
        assert len(all_content) >= len(text)
        # Verify chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i


class TestFixedSizeSplitterEdgeCases:
    """边界情况"""

    def test_one_character_chunk_size(self):
        splitter = FixedSizeSplitter(chunk_size=1, chunk_overlap=0)
        text = "ABC"
        chunks = splitter.split(text)
        assert len(chunks) == 3
        assert chunks[0].content == "A"
        assert chunks[1].content == "B"
        assert chunks[2].content == "C"

    def test_overlap_zero(self):
        splitter = FixedSizeSplitter(chunk_size=10, chunk_overlap=0)
        text = "A" * 25
        chunks = splitter.split(text)
        assert len(chunks) == 3
        assert chunks[0].content == "A" * 10  # 0-10
        assert chunks[1].content == "A" * 10  # 10-20
        assert chunks[2].content == "A" * 5   # 20-25

    def test_whitespace_text(self):
        splitter = FixedSizeSplitter(chunk_size=5, chunk_overlap=1)
        chunks = splitter.split("   ")
        assert len(chunks) == 1
        assert chunks[0].content == "   "

    def test_text_with_newlines(self):
        splitter = FixedSizeSplitter(chunk_size=10, chunk_overlap=2)
        text = "Line1\nLine2\nLine3\nLine4"
        chunks = splitter.split(text)
        assert len(chunks) >= 1
        assert all(c.content for c in chunks)
