from abc import ABC, abstractmethod
from typing import List


class EmbeddingBackend(ABC):
    """Embedding 模型抽象接口"""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        将单条文本转为向量。

        参数:
            text: 输入文本

        返回:
            浮点数向量列表
        """
        ...

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转为向量。

        参数:
            texts: 输入文本列表

        返回:
            浮点数向量列表的列表，顺序与输入一致
        """
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """返回向量的维度数"""
        ...
