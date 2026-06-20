"""PDF 逐页切片器 — PDFPageSplitter

按 PDF 的页面边界切分文本，保留页码信息。

利用 ``sections`` 参数中的 ``page`` 信息将文档按页切分。
如果某页内容超出 ``chunk_size``，则在该页内进一步子切分，
但所有子 chunk 仍携带相同的 ``page_number``。

用法::

    splitter = PDFPageSplitter(chunk_size=1024)
    chunks = splitter.split(text, metadata={"doc_id": "1"}, sections=sections)
    for chunk in chunks:
        print(chunk.metadata["page_number"])
"""

import re
from typing import List, Optional

from app.rag.interfaces.splitter import TextSplitter, DocumentChunk


class PDFPageSplitter(TextSplitter):
    """PDF 逐页感知切片器

    按 sections 中的 page 边界切分，将 ``page_number`` 写入每个 chunk 的 metadata。
    如果某页内容超出 ``chunk_size``，在页内按段落子切分。
    如果未提供 sections 或 sections 为空，回退为 FixedSizeSplitter 行为。
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 0):
        """
        初始化切片器。

        参数:
            chunk_size: 每页内子切分的字符数上限，默认 512
            chunk_overlap: 子切分时的重叠字符数，默认 0

        抛出:
            ValueError: 当 chunk_overlap >= chunk_size 时
        """
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) 必须小于 chunk_size ({chunk_size})"
            )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(
        self,
        text: str,
        metadata: Optional[dict] = None,
        sections: Optional[List[dict]] = None,
    ) -> List[DocumentChunk]:
        """按 PDF 页面边界切分

        参数:
            text: PDF 全文（当 sections 为空时使用）
            metadata: 文档级元数据，合并到每个 chunk
            sections: PDF 解析器的 sections，格式为
                      ``[{"page": 1, "content": "..."}, ...]``

        返回:
            DocumentChunk 列表；空文本返回空列表
        """
        if not text.strip():
            return []

        metadata = metadata or {}
        base_meta = {k: v for k, v in metadata.items() if k != "chunk_size"}

        # 优先使用 sections 中的 page 信息
        if sections and any("page" in s for s in sections):
            return self._split_by_pages(sections, base_meta)

        # 无 sections / 无 page 信息 → 退化为固定大小切分
        return self._fallback_split(text, base_meta)

    # ── 内部方法 ─────────────────────────────────────────────

    def _split_by_pages(
        self,
        sections: List[dict],
        base_meta: dict,
    ) -> List[DocumentChunk]:
        """利用 sections 中的 page 信息按页切分"""
        chunks: List[DocumentChunk] = []
        index = 0

        for sec in sections:
            page_num = sec.get("page", 0)
            content = sec.get("content", "").strip()
            if not content:
                continue

            page_meta = {**base_meta, "page_number": page_num}

            if len(content) <= self._chunk_size:
                chunks.append(
                    DocumentChunk(
                        content=content,
                        chunk_index=index,
                        metadata={**page_meta, "chunk_size": len(content)},
                    )
                )
                index += 1
            else:
                # 页内容超出 chunk_size → 按段落子切分
                sub_chunks = self._split_page_content(content, page_meta, index)
                chunks.extend(sub_chunks)
                index += len(sub_chunks)

        return chunks

    def _split_page_content(
        self,
        content: str,
        page_meta: dict,
        start_index: int,
    ) -> List[DocumentChunk]:
        """将单页内容子切分为多个 chunk（保持 page_number 一致）"""
        paragraphs = re.split(r"\n\n+", content)
        chunks: List[DocumentChunk] = []
        buffer = ""
        idx = start_index

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(buffer) + len(para) + 2 <= self._chunk_size:
                buffer = (buffer + "\n\n" + para).strip() if buffer else para
            else:
                if buffer:
                    chunks.append(
                        DocumentChunk(
                            content=buffer,
                            chunk_index=idx,
                            metadata={**page_meta, "chunk_size": len(buffer)},
                        )
                    )
                    idx += 1
                if len(para) > self._chunk_size:
                    # 单段落超长 → 强行截断
                    for start in range(0, len(para), self._chunk_size):
                        seg = para[start:start + self._chunk_size]
                        chunks.append(
                            DocumentChunk(
                                content=seg,
                                chunk_index=idx,
                                metadata={**page_meta, "chunk_size": len(seg)},
                            )
                        )
                        idx += 1
                    buffer = ""
                else:
                    buffer = para

        if buffer:
            chunks.append(
                DocumentChunk(
                    content=buffer,
                    chunk_index=idx,
                    metadata={**page_meta, "chunk_size": len(buffer)},
                )
            )

        return chunks

    def _fallback_split(
        self,
        text: str,
        base_meta: dict,
    ) -> List[DocumentChunk]:
        """无 sections 时退化为固定大小切分"""
        chunks: List[DocumentChunk] = []
        text_len = len(text)
        start = 0
        index = 0

        while start < text_len:
            end = min(start + self._chunk_size, text_len)
            chunk_text = text[start:end]
            chunks.append(
                DocumentChunk(
                    content=chunk_text,
                    chunk_index=index,
                    metadata={**base_meta, "chunk_size": len(chunk_text)},
                )
            )
            index += 1
            if end >= text_len:
                break
            start = end - self._chunk_overlap

        return chunks

    @property
    def type_name(self) -> str:
        return "pdf_page"
