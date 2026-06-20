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
    """文本切片器抽象接口

    不同文档类型的切片器可以通过可选参数 ``sections`` 获取解析器提取的
    结构化信息（如标题层级、页码等），以实现结构感知的智能切分。
    """

    @abstractmethod
    def split(
        self,
        text: str,
        metadata: Optional[dict] = None,
        sections: Optional[List[dict]] = None,
    ) -> List[DocumentChunk]:
        """
        将输入文本按策略切分为片段列表。

        参数:
            text: 待切分的文本内容
            metadata: 从解析器传递过来的文档元数据，会被合并到每个 chunk 的 metadata 中
            sections: 解析器提取的结构化信息，格式由具体的 (parser, splitter) 策略约定。
                      例如 PDF 的 sections 可能为 ``[{"page": 1, "content": "..."}]``，
                      Markdown 的 sections 可能为 ``[{"heading": "## Title", "level": 2, "content": "..."}]``。
                      切片器可根据此信息做结构感知切分（如按 heading 或 page 边界切分）。

        返回:
            DocumentChunk 列表
        """
        ...

    @property
    @abstractmethod
    def type_name(self) -> str:
        """切片器类型名，用于配置识别（如 "fixed", "markdown", "pdf_page", "semantic"）"""
        ...
