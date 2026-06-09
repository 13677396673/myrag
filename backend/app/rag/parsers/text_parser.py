"""纯文本 / Markdown 解析器 — TextParser

使用 Python 内置 API 读取 ``.txt``、``.md``、``.text``、``.markdown``
文件，无第三方依赖。

用法::

    parser = TextParser()
    doc = parser.parse("README.md")
"""

from typing import List

from app.rag.interfaces.parser import DocumentParser, ParsedDocument


class TextParser(DocumentParser):
    """纯文本 / Markdown 解析器"""

    ENCODING = "utf-8"

    def parse(self, file_path: str) -> ParsedDocument:
        """读取文本文件内容

        参数:
            file_path: 文本文件的完整路径

        返回:
            ParsedDocument，其中 content 为完整文本内容

        异常:
            FileNotFoundError: 文件不存在
        """
        with open(file_path, encoding=self.ENCODING, errors="replace") as f:
            content = f.read()

        return ParsedDocument(content=content, metadata={"source": file_path})

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return [".txt", ".md", ".text", ".markdown"]
