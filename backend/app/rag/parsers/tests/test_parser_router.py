"""ParserRouter 单元测试"""

import pytest

from app.rag.interfaces.parser import DocumentParser
from app.rag.parsers import ParserRouter, TextParser, PDFParser, DocxParser
from app.rag.parsers.parser_router import ParserRouter as ParserRouterCls


class TestParserRouter:
    """ParserRouter 功能测试"""

    # ── 初始化 ────────────────────────────────────────────────

    def test_init_empty_registry(self) -> None:
        """新创建的 ParserRouter 注册表为空"""
        router = ParserRouter()
        assert router.get_supported_extensions() == []

    def test_get_parser_returns_none_for_unregistered(self) -> None:
        """未注册的扩展名返回 None"""
        router = ParserRouter()
        assert router.get_parser(".xyz") is None
        assert router.get_parser(".unknown") is None

    # ── 注册 ────────────────────────────────────────────────

    def test_register_single_parser(self) -> None:
        """注册单个解析器后，其扩展名被正确映射"""
        router = ParserRouter()
        router.register(TextParser)
        exts = router.get_supported_extensions()
        assert ".txt" in exts
        assert ".md" in exts

    def test_register_all_default_parsers(self, parser_router: ParserRouter) -> None:
        """注册所有默认解析器后，扩展名列表包含所有支持的扩展名"""
        exts = parser_router.get_supported_extensions()
        assert ".txt" in exts
        assert ".md" in exts
        assert ".pdf" in exts
        assert ".docx" in exts

    # ── 路由 ────────────────────────────────────────────────

    def test_get_parser_by_extension(self, parser_router: ParserRouter) -> None:
        """根据扩展名正确获取解析器实例"""
        parser = parser_router.get_parser(".txt")
        assert isinstance(parser, TextParser)

        parser = parser_router.get_parser(".pdf")
        assert isinstance(parser, PDFParser)

        parser = parser_router.get_parser(".docx")
        assert isinstance(parser, DocxParser)

    def test_get_parser_case_insensitive(self, parser_router: ParserRouter) -> None:
        """扩展名大小写不敏感"""
        assert isinstance(parser_router.get_parser(".TXT"), TextParser)
        assert isinstance(parser_router.get_parser(".PDF"), PDFParser)
        assert isinstance(parser_router.get_parser(".Docx"), DocxParser)

    def test_get_parser_returns_new_instance_each_call(
        self, parser_router: ParserRouter
    ) -> None:
        """每次调用 get_parser 返回新实例"""
        p1 = parser_router.get_parser(".txt")
        p2 = parser_router.get_parser(".txt")
        assert p1 is not p2
        assert isinstance(p1, TextParser)
        assert isinstance(p2, TextParser)

    def test_get_parser_unsupported_returns_none(
        self, parser_router: ParserRouter
    ) -> None:
        """不支持的扩展名返回 None"""
        assert parser_router.get_parser(".pptx") is None
        assert parser_router.get_parser(".xlsx") is None
        assert parser_router.get_parser(".html") is None

    # ── register 参数校验 ─────────────────────────────────────

    def test_register_non_parser_class_raises_type_error(self) -> None:
        """注册非 DocumentParser 子类抛 TypeError"""
        router = ParserRouter()

        class NotAParser:
            pass

        with pytest.raises(TypeError):
            router.register(NotAParser)  # type: ignore

    def test_register_instance_raises_type_error(self) -> None:
        """注册实例（而非类）抛 TypeError"""
        router = ParserRouter()
        with pytest.raises(TypeError):
            router.register(TextParser())  # type: ignore

    # ── 扩展名覆盖 ────────────────────────────────────────────

    def test_register_overwrites_existing_extension(self) -> None:
        """注册新解析器覆盖已注册的扩展名"""
        router = ParserRouter()
        router.register(TextParser)

        # 自定义解析器覆盖 .txt 扩展名
        class OverrideParser(DocumentParser):
            def parse(self, file_path: str):
                from app.rag.interfaces.parser import ParsedDocument
                return ParsedDocument(content="overridden")

            @classmethod
            def supported_extensions(cls):
                return [".txt"]

        router.register(OverrideParser)
        parser = router.get_parser(".txt")
        assert isinstance(parser, OverrideParser)
        doc = parser.parse("/fake/path.txt")
        assert doc.content == "overridden"

    # ── 扩展名列表示例 ────────────────────────────────────────

    def test_get_supported_extensions_sorted(self) -> None:
        """get_supported_extensions 返回排序后的列表"""
        router = ParserRouter()
        router.register(PDFParser)
        router.register(TextParser)
        exts = router.get_supported_extensions()
        # .md, .pdf, .text, .txt, .markdown
        assert exts == sorted(exts)
