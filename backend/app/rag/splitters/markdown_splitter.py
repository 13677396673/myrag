"""Markdown 结构切片器 — MarkdownSplitter

按 Markdown 标题结构（``#`` ~ ``######``）进行切分，保留文档层级信息。

每个 chunk 的 metadata 中包含其所在标题层级链（如 ``h1``、``h2`` 等），
方便检索时结合上下文。如果某个 section 的内容超出 ``chunk_size``，
则在该 section 内部按段落（``\\n\\n``）进一步子切分。

用法::

    splitter = MarkdownSplitter(chunk_size=512)
    chunks = splitter.split(text, metadata={"doc_id": "1"}, sections=sections)
    for chunk in chunks:
        print(chunk.metadata["h1"], chunk.metadata.get("h2"))
"""

import re
from typing import Dict, List, Optional

from app.rag.interfaces.splitter import TextSplitter, DocumentChunk


class MarkdownSplitter(TextSplitter):
    """Markdown 结构感知切片器

    按标题切分，保留 ``h1`` ~ ``h6`` 层级链到每个 chunk 的 metadata 中。
    当 sections 参数提供 heading 信息时优先使用；否则从 text 中自行解析。
    """

    # 匹配行首的 # 标题
    _HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 0):
        """
        初始化切片器。

        参数:
            chunk_size: 每个切片的字符数上限，默认 512
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
        """按 Markdown 标题结构切分文本

        参数:
            text: Markdown 全文
            metadata: 文档级元数据，合并到每个 chunk
            sections: 解析器提供的结构化信息。如果包含 ``heading`` 和 ``level``
                      字段则优先使用；否则从 text 中自行解析标题边界。

        返回:
            DocumentChunk 列表；空文本返回空列表
        """
        if not text.strip():
            return []

        metadata = metadata or {}
        base_meta = {k: v for k, v in metadata.items() if k != "chunk_size"}

        if sections:
            return self._split_by_sections(sections, base_meta)
        else:
            return self._split_by_parsing(text, base_meta)

    # ── 内部方法 ─────────────────────────────────────────────

    def _split_by_sections(
        self,
        sections: List[dict],
        base_meta: dict,
    ) -> List[DocumentChunk]:
        """利用 sections 中的 heading 信息切分"""
        chunks: List[DocumentChunk] = []
        index = 0
        heading_chain: Dict[str, str] = {}

        for sec in sections:
            # 更新当前标题链（去除 # 标记保留纯文本，与自解析路径一致）
            level = sec.get("level", 0)
            raw_heading = sec.get("heading", "")
            heading_text = re.sub(r"^#+\s*", "", raw_heading).strip() or raw_heading
            if level and heading_text:
                _update_heading_chain(heading_chain, level, heading_text)

            content = sec.get("content", "").strip()
            if not content:
                continue

            # 将当前 section 的内容按 chunk_size 子切分
            sub_chunks = self._sub_split_content(
                content, base_meta, heading_chain, index
            )
            chunks.extend(sub_chunks)
            index += len(sub_chunks)

        return chunks

    def _split_by_parsing(
        self,
        text: str,
        base_meta: dict,
    ) -> List[DocumentChunk]:
        """从纯文本中自行解析标题边界并切分"""
        # 找到所有标题的位置
        matches = list(self._HEADING_PATTERN.finditer(text))
        if not matches:
            # 没有标题 → 整个文本作为一段（或子切分）
            return self._sub_split_content(text, base_meta, {}, 0)

        chunks: List[DocumentChunk] = []
        index = 0
        heading_chain: Dict[str, str] = {}

        for i, match in enumerate(matches):
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            _update_heading_chain(heading_chain, level, heading_text)

            # 当前 section 的起始位置
            start = match.end() + 1  # 跳过标题行本身
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            if not content:
                content = ""  # 空 section 也生成一个带标题的 chunk

            # 将 section 内容子切分
            sub_chunks = self._sub_split_content(
                content, base_meta, heading_chain, index,
            )
            if not sub_chunks and content == "":
                # 纯空 section → 还是生成一个 chunk 用于保留标题信息
                sub_chunks = [
                    DocumentChunk(
                        content="",
                        chunk_index=index,
                        metadata={
                            **base_meta,
                            **heading_chain,
                            "heading": heading_text,
                            "heading_level": level,
                        },
                    )
                ]
            chunks.extend(sub_chunks)
            index += len(sub_chunks)

        return chunks

    def _sub_split_content(
        self,
        content: str,
        base_meta: dict,
        heading_chain: Dict[str, str],
        start_index: int,
    ) -> List[DocumentChunk]:
        """将一个 section 的内容按 chunk_size 子切分（如果过长）"""
        if not content:
            return []

        if len(content) <= self._chunk_size:
            meta = {
                **base_meta,
                **heading_chain,
            }
            if "heading" in heading_chain:
                meta["heading"] = heading_chain.get(
                    f"h{max([int(k[1:]) for k in heading_chain.keys() if k.startswith('h')], default=1)}",
                    "",
                )
            return [
                DocumentChunk(
                    content=content,
                    chunk_index=start_index,
                    metadata={
                        **meta,
                        "chunk_size": len(content),
                    },
                )
            ]

        # 超出 chunk_size → 按段落子切分
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
                            metadata={
                                **base_meta,
                                **heading_chain,
                                "chunk_size": len(buffer),
                            },
                        )
                    )
                    idx += 1
                # 单个段落也超 chunk_size → 强行截断
                if len(para) > self._chunk_size:
                    for start in range(0, len(para), self._chunk_size):
                        seg = para[start:start + self._chunk_size]
                        chunks.append(
                            DocumentChunk(
                                content=seg,
                                chunk_index=idx,
                                metadata={
                                    **base_meta,
                                    **heading_chain,
                                    "chunk_size": len(seg),
                                },
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
                    metadata={
                        **base_meta,
                        **heading_chain,
                        "chunk_size": len(buffer),
                    },
                )
            )

        return chunks

    @property
    def type_name(self) -> str:
        return "markdown"


def _update_heading_chain(
    chain: Dict[str, str],
    level: int,
    heading_text: str,
) -> None:
    """更新标题层级链。

    例如碰到 ``### 特性``（level=3）时：
    - 保留 h1、h2（更高层级不变）
    - 设置 h3 = "特性"
    - 清除 h4、h5、h6（更低层级失效）
    """
    for lv in range(level, 7):
        chain.pop(f"h{lv}", None)
    chain[f"h{level}"] = heading_text
