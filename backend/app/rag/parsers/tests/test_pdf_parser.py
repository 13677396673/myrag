"""PDFParser 单元测试"""

import os

import pytest

from app.rag.interfaces.parser import ParsedDocument
from app.rag.parsers.pdf_parser import PDFParser


class TestPDFParser:
    """PDFParser 功能测试"""

    @pytest.fixture
    def parser(self) -> PDFParser:
        return PDFParser()

    # ── 正常解析 ──────────────────────────────────────────────

    def test_parse_pdf_returns_parsed_document(
        self, parser: PDFParser, sample_pdf_path: str
    ) -> None:
        """解析 PDF 返回正确的 ParsedDocument"""
        doc = parser.parse(sample_pdf_path)
        assert isinstance(doc, ParsedDocument)
        assert isinstance(doc.content, str)
        assert len(doc.content) > 0

    def test_parse_pdf_content(self, parser: PDFParser, sample_pdf_path: str) -> None:
        """PDF 文本内容正确包含各页文字"""
        doc = parser.parse(sample_pdf_path)
        assert "Page 1 Content Here" in doc.content
        assert "Page 2 Content Here" in doc.content
        assert "Page 3 Content Here" in doc.content

    # ── Sections ──────────────────────────────────────────────

    def test_sections_contain_page_info(
        self, parser: PDFParser, sample_pdf_path: str
    ) -> None:
        """sections 包含页码信息"""
        doc = parser.parse(sample_pdf_path)
        assert len(doc.sections) > 0
        assert doc.sections[0]["page"] == 1
        for section in doc.sections:
            assert "page" in section
            assert "content" in section

    def test_sections_count(self, parser: PDFParser, sample_pdf_path: str) -> None:
        """3 页 PDF 应生成 3 个 section"""
        doc = parser.parse(sample_pdf_path)
        assert len(doc.sections) == 3

    # ── Metadata ──────────────────────────────────────────────

    def test_metadata_contains_total_pages(
        self, parser: PDFParser, sample_pdf_path: str
    ) -> None:
        """metadata 包含 total_pages"""
        doc = parser.parse(sample_pdf_path)
        assert doc.metadata.get("total_pages") == 3
        assert doc.metadata.get("source") == sample_pdf_path

    # ── 异常处理 ──────────────────────────────────────────────

    def test_parse_nonexistent_file(self, parser: PDFParser) -> None:
        """不存在的文件抛出异常"""
        with pytest.raises(Exception):
            parser.parse("/nonexistent/path/file.pdf")

    # ── 扩展名 ────────────────────────────────────────────────

    def test_supported_extensions(self, parser: PDFParser) -> None:
        """supported_extensions 只返回 ['.pdf']"""
        exts = parser.supported_extensions()
        assert exts == [".pdf"]
