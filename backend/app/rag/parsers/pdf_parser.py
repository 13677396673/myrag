"""PDF 解析器 — PDFParser

基于 PyMuPDF (fitz) 逐页提取 PDF 文本内容，并为每一页生成结构化 section。

用法::

    parser = PDFParser()
    doc = parser.parse("report.pdf")
    # doc.content        → 所有页文本
    # doc.sections       → [{"page": 1, "content": "..."}, ...]
    # doc.metadata       → {"total_pages": 10, "title": "...", ...}
"""

from typing import List

import fitz  # PyMuPDF

from app.rag.interfaces.parser import DocumentParser, ParsedDocument


class PDFParser(DocumentParser):
    """PDF 文档解析器（依赖 PyMuPDF）"""

    def parse(self, file_path: str) -> ParsedDocument:
        """解析 PDF 文件

        逐页提取文本，生成含页码信息的 sections，并收集文档元数据。

        参数:
            file_path: PDF 文件的完整路径

        返回:
            ParsedDocument，包含完整文本、逐页 sections 和元数据

        异常:
            FileNotFoundError: 文件不存在
        """
        doc = fitz.open(file_path)
        total_pages = len(doc)

        all_text: List[str] = []
        sections: List[dict] = []

        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()

            # 跳过空白页（没有可提取文本）
            if text.strip():
                all_text.append(text)
                sections.append({
                    "page": page_num + 1,
                    "content": text,
                })

        # 收集元数据
        metadata = {
            "source": file_path,
            "total_pages": total_pages,
            "title": doc.metadata.get("title", "") or "",
            "author": doc.metadata.get("author", "") or "",
        }

        doc.close()

        return ParsedDocument(
            content="\n".join(all_text),
            metadata=metadata,
            sections=sections,
        )

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return [".pdf"]
