"""
固定大小文本切片器

按固定字符数（chunk_size）切分文本，支持相邻片段之间的重叠（overlap）。
MVP 阶段使用字符数而非 token 数进行切分，以降低依赖复杂度。
"""

from typing import List, Optional

from app.rag.interfaces.splitter import TextSplitter, DocumentChunk


class FixedSizeSplitter(TextSplitter):
    """固定大小切片器：按 chunk_size 切分，支持 overlap"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        """
        初始化切片器。

        参数:
            chunk_size: 每个切片的字符数，默认 512
            chunk_overlap: 相邻切片的重叠字符数，默认 64

        抛出:
            ValueError: 当 chunk_overlap >= chunk_size 时
        """
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) 必须小于 chunk_size ({chunk_size})"
            )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, text: str, metadata: Optional[dict] = None) -> List[DocumentChunk]:
        """
        将输入文本按固定大小切分为片段列表。

        参数:
            text: 待切分的文本内容
            metadata: 从解析器传递过来的文档元数据，
                      会被合并到每个 chunk 的 metadata 中

        返回:
            DocumentChunk 列表；空文本返回空列表
        """
        if not text:
            return []

        chunks: List[DocumentChunk] = []
        metadata = metadata or {}
        text_len = len(text)
        start = 0
        index = 0

        while start < text_len:
            end = start + self._chunk_size
            chunk_text = text[start:end]
            chunks.append(
                DocumentChunk(
                    content=chunk_text,
                    chunk_index=index,
                    metadata={
                        **metadata,
                        "chunk_size": len(chunk_text),
                    },
                )
            )
            index += 1
            if end >= text_len:
                break
            start = end - self._chunk_overlap

        return chunks

    @property
    def type_name(self) -> str:
        return "fixed"
