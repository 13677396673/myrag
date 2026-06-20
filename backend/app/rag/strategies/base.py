"""ChunkingStrategy 数据类

将一个 ``DocumentParser`` 和一个 ``TextSplitter`` 配对，
表示一种文档类型的完整处理策略。
"""

from dataclasses import dataclass
from typing import List

from app.rag.interfaces.parser import DocumentParser
from app.rag.interfaces.splitter import TextSplitter, DocumentChunk


@dataclass
class ChunkingStrategy:
    """文档 chunking 策略

    将解析器和切片器配对，共同处理一种或多种文档类型。
    (parser, splitter) 之间通过 ``ParsedDocument.sections``
    的结构约定协作——splitter 知道 parser 产出的 sections 格式。

    参数:
        name: 策略名称，如 ``"markdown"``、``"pdf"``、``"text"``
        parser: 文档解析器实例
        splitter: 文本切片器实例
        description: 策略描述（可选）
    """

    name: str
    parser: DocumentParser
    splitter: TextSplitter
    description: str = ""

    def execute(
        self,
        file_path: str,
        metadata: dict,
    ) -> List[DocumentChunk]:
        """执行完整的解析 + 切分流程

        参数:
            file_path: 文件的完整路径
            metadata: 文档级元数据，会被合并到每个 chunk

        返回:
            DocumentChunk 列表
        """
        parsed = self.parser.parse(file_path)
        if not parsed.content.strip():
            return []
        return self.splitter.split(
            text=parsed.content,
            metadata=metadata,
            sections=parsed.sections,
        )
