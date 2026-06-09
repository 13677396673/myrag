"""文档解析器模块

提供 ``ParserRouter`` 路由及 ``TextParser``、``PDFParser``、``DocxParser``
三种内置解析器实现，支持运行时动态注册新解析器。

用法::

    from app.rag.parsers import ParserRouter, register_default_parsers

    router = ParserRouter()
    register_default_parsers(router)
    parser = router.get_parser(".pdf")
    doc = parser.parse("report.pdf")
"""

from .parser_router import ParserRouter
from .text_parser import TextParser
from .pdf_parser import PDFParser
from .docx_parser import DocxParser

__all__ = [
    "ParserRouter",
    "TextParser",
    "PDFParser",
    "DocxParser",
    "register_default_parsers",
]


def register_default_parsers(router: ParserRouter) -> None:
    """注册内置解析器到路由

    将 ``TextParser``、``PDFParser``、``DocxParser`` 三个解析器
    注册到给定的 ``ParserRouter`` 实例中。

    参数:
        router: 待注册的 ``ParserRouter`` 实例
    """
    router.register(TextParser)
    router.register(PDFParser)
    router.register(DocxParser)
