"""MarkdownSplitter 单元测试

测试内容：
1. 按标题边界切分
2. 标题层级链正确传递到 chunk metadata
3. sections 方式 vs 自解析方式结果一致
4. 无标题文档回退行为
5. 长 section 子切分
6. sections 为空时回退自解析
"""

import pytest

from app.rag.splitters.markdown_splitter import MarkdownSplitter


class TestMarkdownSplitterInit:
    """初始化测试"""

    def test_default_params(self):
        splitter = MarkdownSplitter()
        assert splitter.type_name == "markdown"

    def test_custom_chunk_size(self):
        splitter = MarkdownSplitter(chunk_size=256)
        assert splitter._chunk_size == 256

    def test_overlap_equals_chunk_size_raises(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            MarkdownSplitter(chunk_size=100, chunk_overlap=100)

    def test_overlap_greater_than_chunk_size_raises(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            MarkdownSplitter(chunk_size=100, chunk_overlap=200)


class TestMarkdownSplitterSplit:
    """切片逻辑测试"""

    def test_empty_text_returns_empty(self):
        splitter = MarkdownSplitter()
        assert splitter.split("") == []
        assert splitter.split("   ") == []

    def test_no_headings_returns_one_chunk(self):
        splitter = MarkdownSplitter(chunk_size=1000)
        text = "这是一段纯文本，没有标题。\n\n第二段落。"
        chunks = splitter.split(text)
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert "纯文本" in chunks[0].content

    def test_split_by_headings(self):
        splitter = MarkdownSplitter(chunk_size=1000)
        text = """# 第一章

这是第一章的内容。

## 第一节

第一节的具体内容。

## 第二节

第二节的内容。

# 第二章

第二章的内容。"""
        chunks = splitter.split(text)
        # 有 4 个标题 → 4 个 sections
        assert len(chunks) == 4
        assert chunks[0].metadata.get("h1") == "第一章"
        assert chunks[1].metadata.get("h1") == "第一章"
        assert chunks[1].metadata.get("h2") == "第一节"
        assert chunks[2].metadata.get("h2") == "第二节"
        assert chunks[3].metadata.get("h1") == "第二章"

    def test_heading_chain_hierarchy(self):
        """测试标题层级链正确更新"""
        splitter = MarkdownSplitter(chunk_size=1000)
        text = """# Title

intro

## Section 1

content 1

### Subsection

sub content

## Section 2

content 2"""
        chunks = splitter.split(text)
        assert len(chunks) == 4

        # h1 始终为 "Title"
        for c in chunks:
            assert c.metadata.get("h1") == "Title"

        # Section 1 下的 subsections
        assert chunks[1].metadata.get("h2") == "Section 1"
        assert chunks[2].metadata.get("h2") == "Section 1"
        assert chunks[2].metadata.get("h3") == "Subsection"
        # Section 2 时 h3 应被清除
        assert "h3" not in chunks[3].metadata
        assert chunks[3].metadata.get("h2") == "Section 2"

    def test_section_content_sub_split(self):
        """测试长 section 内容被子切分"""
        splitter = MarkdownSplitter(chunk_size=50)
        text = "# 标题\n\n" + "A" * 200
        chunks = splitter.split(text)
        # 200 字符按 50 切分 → 至少 4 个 chunk
        assert len(chunks) >= 4
        for c in chunks:
            assert c.metadata.get("h1") == "标题"

    def test_sections_param_overrides_parsing(self):
        """测试传入 sections 时优先使用 sections 而非自解析"""
        splitter = MarkdownSplitter(chunk_size=1000)
        text = "dummy content"

        sections = [
            {"heading": "# Title", "level": 1, "content": "Intro paragraph."},
            {"heading": "## Section A", "level": 2, "content": "Section A body."},
            {"heading": "## Section B", "level": 2, "content": "Section B body."},
        ]

        chunks = splitter.split(text, sections=sections)
        assert len(chunks) == 3
        assert chunks[0].metadata.get("h1") == "Title"
        assert chunks[1].metadata.get("h2") == "Section A"
        assert chunks[2].metadata.get("h2") == "Section B"

    def test_metadata_preserved_in_sub_chunks(self):
        """测试子切分时 metadata 中的标题链正确传递"""
        splitter = MarkdownSplitter(chunk_size=30)
        text = "## Section\n\n" + "B" * 100
        chunks = splitter.split(text)
        for c in chunks:
            assert c.metadata.get("h2") == "Section"

    def test_no_heading_chunk_size_oversized(self):
        """测试无标题但内容超长的文档"""
        splitter = MarkdownSplitter(chunk_size=30)
        text = "Word. " * 20
        chunks = splitter.split(text)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c.content) <= 30 + 2  # 允许边界溢出

    def test_sections_with_long_content_sub_split(self):
        """测试通过 sections 传入时，长内容子切分"""
        splitter = MarkdownSplitter(chunk_size=30)
        sections = [
            {"heading": "# Title", "level": 1, "content": "A" * 100},
        ]
        chunks = splitter.split("dummy", sections=sections)
        assert len(chunks) >= 3
        for c in chunks:
            assert c.metadata.get("h1") == "Title"
