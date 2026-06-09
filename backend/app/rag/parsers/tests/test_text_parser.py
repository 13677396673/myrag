"""TextParser 单元测试"""

import pytest

from app.rag.interfaces.parser import ParsedDocument
from app.rag.parsers.text_parser import TextParser


class TestTextParser:
    """TextParser 功能测试"""

    @pytest.fixture
    def parser(self) -> TextParser:
        return TextParser()

    # ── 正常解析 ──────────────────────────────────────────────

    def test_parse_txt(self, parser: TextParser, sample_txt_path: str) -> None:
        """解析 .txt 文件返回正确的 ParsedDocument"""
        doc = parser.parse(sample_txt_path)
        assert isinstance(doc, ParsedDocument)
        assert isinstance(doc.content, str)
        assert len(doc.content) > 0
        assert "Hello, this is a sample text file." in doc.content
        assert "中文测试" in doc.content
        assert doc.metadata.get("source") == sample_txt_path

    def test_parse_md(self, parser: TextParser, sample_md_path: str) -> None:
        """解析 .md 文件返回正确的 ParsedDocument"""
        doc = parser.parse(sample_md_path)
        assert isinstance(doc, ParsedDocument)
        assert len(doc.content) > 0
        assert "# Sample Markdown" in doc.content
        assert "Section 1" in doc.content
        assert doc.metadata.get("source") == sample_md_path

    def test_parse_empty_file(self, parser: TextParser, empty_txt_path: str) -> None:
        """空文件解析后 content 为空字符串"""
        doc = parser.parse(empty_txt_path)
        assert doc.content == ""

    # ── 异常处理 ──────────────────────────────────────────────

    def test_parse_nonexistent_file(self, parser: TextParser) -> None:
        """不存在的文件抛 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/path/file.txt")

    # ── ParsedDocument 结构 ──────────────────────────────────

    def test_parsed_document_structure(self, parser: TextParser, sample_txt_path: str) -> None:
        """验证 ParsedDocument 的 content 包含完整文本"""
        doc = parser.parse(sample_txt_path)
        assert doc.content is not None
        assert len(doc.content) > 0
        # metadata 包含 source
        assert "source" in doc.metadata
        # sections 为空（TextParser 不分段）
        assert doc.sections == []
