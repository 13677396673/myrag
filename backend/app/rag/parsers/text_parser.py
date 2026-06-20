"""纯文本 / Markdown 解析器 — TextParser

使用 Python 内置 API 读取 ``.txt``、``.md``、``.text``、``.markdown``
文件，无第三方依赖。

对 ``.md`` / ``.markdown`` 文件会额外解析标题结构（``#`` ~ ``######``），
生成含 heading 层级信息的 ``sections``，供 MarkdownSplitter 等结构感知
切片器使用。

用法::

    parser = TextParser()
    doc = parser.parse("README.md")
    # doc.sections → [{"heading": "# Title", "level": 1, "content": "..."}, ...]
"""

import os
import re
from typing import List

from app.rag.interfaces.parser import DocumentParser, ParsedDocument


class TextParser(DocumentParser):
    """纯文本 / Markdown 解析器"""

    ENCODING = "utf-8"

    # 匹配行首的 # 标题
    _HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def parse(self, file_path: str) -> ParsedDocument:
        """读取文本文件内容

        对 ``.md`` / ``.markdown`` 文件，额外解析标题结构填充 sections。

        参数:
            file_path: 文本文件的完整路径

        返回:
            ParsedDocument，其中 content 为完整文本内容，
            sections 在 .md 文件中包含标题层级信息

        异常:
            FileNotFoundError: 文件不存在
        """
        with open(file_path, encoding=self.ENCODING, errors="replace") as f:
            content = f.read()

        ext = os.path.splitext(file_path)[1].lower()
        sections: List[dict] = []

        if ext in (".md", ".markdown"):
            sections = self._parse_markdown_sections(content)

        return ParsedDocument(
            content=content,
            metadata={"source": file_path},
            sections=sections,
        )

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return [".txt", ".md", ".text", ".markdown"]

    # ── Markdown 标题解析 ──────────────────────────────────────

    def _parse_markdown_sections(self, content: str) -> List[dict]:
        """将 Markdown 文本解析为标题结构的 sections 列表

        返回::

            [
                {"heading": "# Title", "level": 1, "content": "intro paragraph..."},
                {"heading": "## Section 1", "level": 2, "content": "section body..."},
                ...
            ]
        """
        matches = list(self._HEADING_PATTERN.finditer(content))
        if not matches:
            # 无标题 → 整个文档作为一个 section
            return [{"heading": "", "level": 0, "content": content.strip()}]

        sections: List[dict] = []
        for i, match in enumerate(matches):
            heading_text = match.group(0).strip()  # 完整标题行，如 "## Section 1"
            level = len(match.group(1))  # # 的个数
            # 当前 heading 之后的内容起点（跳过标题行本身）
            start = match.end() + 1
            # 内容截止到下一个 heading 之前
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_content = content[start:end].strip()

            sections.append({
                "heading": heading_text,
                "level": level,
                "content": section_content,
            })

        return sections
