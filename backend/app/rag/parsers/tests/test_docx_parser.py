"""DocxParser 单元测试"""

import pytest

from app.rag.interfaces.parser import ParsedDocument
from app.rag.parsers.docx_parser import DocxParser


class TestDocxParser:
    """DocxParser 功能测试"""

    @pytest.fixture
    def parser(self) -> DocxParser:
        return DocxParser()

    # ── 正常解析 ──────────────────────────────────────────────

    def test_parse_docx_returns_parsed_document(
        self, parser: DocxParser, sample_docx_path: str
    ) -> None:
        """解析 .docx 返回正确的 ParsedDocument"""
        doc = parser.parse(sample_docx_path)
        assert isinstance(doc, ParsedDocument)
        assert isinstance(doc.content, str)
        assert len(doc.content) > 0

    def test_parse_docx_content(self, parser: DocxParser, sample_docx_path: str) -> None:
        """解析结果包含文档中的文本"""
        doc = parser.parse(sample_docx_path)
        # 标题如果被 python-docx 提取为段落，应该包含 "Test Document"
        # 但 heading 在 python-docx 中可能是段落，也可能需要单独处理
        assert "This is a test paragraph for DOCX parsing." in doc.content
        assert "中文" in doc.content

    def test_paragraph_count(self, parser: DocxParser, sample_docx_path: str) -> None:
        """metadata 中包含段落计数"""
        doc = parser.parse(sample_docx_path)
        assert doc.metadata.get("paragraphs", 0) > 0

    # ── Metadata ──────────────────────────────────────────────

    def test_metadata_contains_source(
        self, parser: DocxParser, sample_docx_path: str
    ) -> None:
        """metadata 包含 source"""
        doc = parser.parse(sample_docx_path)
        assert doc.metadata.get("source") == sample_docx_path

    # ── 异常处理 ──────────────────────────────────────────────

    def test_parse_nonexistent_file(self, parser: DocxParser) -> None:
        """不存在的文件抛出异常"""
        with pytest.raises(Exception):
            parser.parse("/nonexistent/path/file.docx")

    # ── 扩展名 ────────────────────────────────────────────────

    def test_supported_extensions(self, parser: DocxParser) -> None:
        """supported_extensions 只返回 ['.docx']"""
        exts = parser.supported_extensions()
        assert exts == [".docx"]
