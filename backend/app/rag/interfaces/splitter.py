from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DocumentChunk:
    """文档切片"""
    content: str                                # 切片文本内容
    chunk_index: int                            # 切片序号
    metadata: dict = field(default_factory=dict)  # {document_id, page_number, heading, ...}


class TextSplitter(ABC):
    """文本切片器抽象接口"""

    @abstractmethod
    def split(self, text: str, metadata: Optional[dict] = None) -> List[DocumentChunk]:
        """
        将输入文本按策略切分为片段列表。

        参数:
            text: 待切分的文本内容
            metadata: 从解析器传递过来的文档元数据，会被合并到每个 chunk 的 metadata 中

        返回:
            DocumentChunk 列表
        """
        ...

    @property
    @abstractmethod
    def type_name(self) -> str:
        """切片器类型名，用于配置识别（如 "fixed", "markdown", "semantic"）"""
        ...
