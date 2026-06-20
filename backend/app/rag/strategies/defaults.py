"""内置默认 chunking 策略注册

为每种支持的文档类型注册合适的 (parser, splitter) 配对：

============ ================ =================== =====================
扩展名        策略名称          解析器               切片器
============ ================ =================== =====================
.txt/.text   "text"           TextParser          FixedSizeSplitter
.md/.markdown "markdown"      TextParser          MarkdownSplitter
.pdf         "pdf"            PDFParser           PDFPageSplitter
.docx        "docx"           DocxParser          FixedSizeSplitter
============ ================ =================== =====================
"""

from typing import Optional

from app.rag.parsers import TextParser, PDFParser, DocxParser
from app.rag.splitters import FixedSizeSplitter
from app.rag.splitters.markdown_splitter import MarkdownSplitter
from app.rag.splitters.pdf_page_splitter import PDFPageSplitter
from app.rag.strategies.base import ChunkingStrategy
from app.rag.strategies.router import StrategyRouter


def register_default_strategies(
    router: StrategyRouter,
    *,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    md_chunk_size: Optional[int] = None,
    pdf_chunk_size: Optional[int] = None,
) -> None:
    """注册内置 chunking 策略到路由

    参数:
        router: StrategyRouter 实例
        chunk_size: 通用切片大小（默认 512）
        chunk_overlap: 通用切片重叠（默认 64）
        md_chunk_size: Markdown 切片大小，不传则使用 chunk_size
        pdf_chunk_size: PDF 切片大小，不传则使用 chunk_size
    """
    md_size = md_chunk_size or chunk_size
    pdf_size = pdf_chunk_size or chunk_size

    # 1. 纯文本策略 — FixedSizeSplitter，不感知结构
    router.register(
        [".txt", ".text"],
        ChunkingStrategy(
            name="text",
            parser=TextParser(),
            splitter=FixedSizeSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            ),
            description="通用文本，按固定大小切分",
        ),
    )

    # 2. Markdown 策略 — MarkdownSplitter，标题感知
    router.register(
        [".md", ".markdown"],
        ChunkingStrategy(
            name="markdown",
            parser=TextParser(),
            splitter=MarkdownSplitter(
                chunk_size=md_size,
            ),
            description="Markdown 文档，按标题结构切分",
        ),
    )

    # 3. PDF 策略 — PDFPageSplitter，页码感知
    router.register(
        [".pdf"],
        ChunkingStrategy(
            name="pdf",
            parser=PDFParser(),
            splitter=PDFPageSplitter(
                chunk_size=pdf_size,
            ),
            description="PDF 文档，按页面边界切分",
        ),
    )

    # 4. DOCX 策略 — FixedSizeSplitter（暂不感知结构）
    router.register(
        [".docx"],
        ChunkingStrategy(
            name="docx",
            parser=DocxParser(),
            splitter=FixedSizeSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            ),
            description="Word 文档，按固定大小切分（暂不支持结构感知）",
        ),
    )
