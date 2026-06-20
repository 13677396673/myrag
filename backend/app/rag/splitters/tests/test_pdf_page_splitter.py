"""PDFPageSplitter 单元测试

测试内容：
1. 按 page 边界切分
2. page_number 写入 chunk metadata
3. 长页内容子切分后 page_number 保持一致
4. 无 sections / 无 page 信息时回退固定大小切分
5. 空文档
"""

import pytest

from app.rag.splitters.pdf_page_splitter import PDFPageSplitter


class TestPDFPageSplitterInit:
    """初始化测试"""

    def test_default_params(self):
        splitter = PDFPageSplitter()
        assert splitter.type_name == "pdf_page"

    def test_custom_chunk_size(self):
        splitter = PDFPageSplitter(chunk_size=256)
        assert splitter._chunk_size == 256

    def test_overlap_equals_chunk_size_raises(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            PDFPageSplitter(chunk_size=100, chunk_overlap=100)

    def test_overlap_greater_than_chunk_size_raises(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            PDFPageSplitter(chunk_size=100, chunk_overlap=200)


class TestPDFPageSplitterSplit:
    """切片逻辑测试"""

    def test_empty_text_returns_empty(self):
        splitter = PDFPageSplitter()
        assert splitter.split("") == []
        assert splitter.split("   ") == []

    def test_split_by_pages(self):
        """测试按 page 边界切分"""
        splitter = PDFPageSplitter(chunk_size=1000)
        sections = [
            {"page": 1, "content": "第一页的内容。"},
            {"page": 2, "content": "第二页的内容。"},
            {"page": 3, "content": "第三页的内容。"},
        ]
        chunks = splitter.split("dummy", sections=sections)
        assert len(chunks) == 3
        assert chunks[0].metadata["page_number"] == 1
        assert chunks[1].metadata["page_number"] == 2
        assert chunks[2].metadata["page_number"] == 3

    def test_page_number_in_all_chunks(self):
        """测试 page_number 在 metadata 中"""
        splitter = PDFPageSplitter(chunk_size=1000)
        sections = [
            {"page": 5, "content": "第五页内容"},
        ]
        chunks = splitter.split("dummy", sections=sections)
        assert chunks[0].metadata["page_number"] == 5

    def test_long_page_sub_split_preserves_page_number(self):
        """测试长页子切分后所有子 chunk 的 page_number 一致"""
        splitter = PDFPageSplitter(chunk_size=30)
        sections = [
            {"page": 1, "content": "A " * 50},
        ]
        chunks = splitter.split("dummy", sections=sections)
        assert len(chunks) >= 2
        for c in chunks:
            assert c.metadata["page_number"] == 1

    def test_empty_page_skipped(self):
        """测试空白页被跳过"""
        splitter = PDFPageSplitter(chunk_size=1000)
        sections = [
            {"page": 1, "content": "有内容"},
            {"page": 2, "content": "   "},  # 空白页
            {"page": 3, "content": "也有内容"},
        ]
        chunks = splitter.split("dummy", sections=sections)
        assert len(chunks) == 2
        assert chunks[0].metadata["page_number"] == 1
        assert chunks[1].metadata["page_number"] == 3

    def test_fallback_no_sections(self):
        """测试无 sections 时退化为固定大小切分"""
        splitter = PDFPageSplitter(chunk_size=30)
        text = "Hello world. " * 10
        chunks = splitter.split(text, sections=[])
        assert len(chunks) >= 2
        # 回退模式下没有 page_number
        assert "page_number" not in chunks[0].metadata

    def test_fallback_no_page_key_in_sections(self):
        """测试 sections 中无 page 字段时退化为固定大小切分"""
        splitter = PDFPageSplitter(chunk_size=1000)
        sections = [
            {"content": "只有内容没有页码"},
            {"content": "第二条"},
        ]
        chunks = splitter.split("dummy", sections=sections)
        assert len(chunks) >= 1
        # 退化为固定切分，没有 page_number

    def test_multiple_pages_with_sub_split(self):
        """测试多页都有长内容"""
        splitter = PDFPageSplitter(chunk_size=30)
        sections = [
            {"page": 1, "content": "X " * 30},
            {"page": 2, "content": "Y " * 30},
        ]
        chunks = splitter.split("dummy", sections=sections)
        assert len(chunks) >= 4
        # 验证每页的 chunks 页码正确
        for c in chunks:
            assert c.metadata["page_number"] in (1, 2)

    def test_metadata_forwarded_to_chunks(self):
        """测试 metadata 正确传递到每个 chunk"""
        splitter = PDFPageSplitter(chunk_size=1000)
        sections = [
            {"page": 1, "content": "内容"},
        ]
        chunks = splitter.split("dummy", metadata={"doc_id": "doc-1"}, sections=sections)
        assert chunks[0].metadata["doc_id"] == "doc-1"
        assert chunks[0].metadata["page_number"] == 1
