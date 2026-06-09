from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class ParsedDocument:
    """文档解析后的结构化输出"""
    content: str                                # 完整文本内容
    metadata: dict = field(default_factory=dict)  # {title, author, total_pages, ...}
    sections: List[dict] = field(default_factory=list)  # [{"heading": "...", "content": "...", "page": 1}]


class DocumentParser(ABC):
    """文档解析器抽象接口"""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """
        解析指定路径的文件。

        参数:
            file_path: 文件的完整路径

        返回:
            包含文本内容和结构化元数据的 ParsedDocument

        异常:
            FileNotFoundError: 文件不存在
            ParseError: 解析过程出错
        """
        ...

    @classmethod
    @abstractmethod
    def supported_extensions(cls) -> List[str]:
        """
        返回支持的文件扩展名列表。

        返回:
            如 ['.txt', '.md', '.pdf']
        """
        ...
