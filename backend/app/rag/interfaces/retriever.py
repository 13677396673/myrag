from abc import ABC, abstractmethod
from typing import List, Optional

from .vector_store import SearchResult


class Retriever(ABC):
    """检索器抽象接口"""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_conditions: Optional[dict] = None,
    ) -> List[SearchResult]:
        """
        根据查询文本检索相关文档片段。

        参数:
            query: 用户查询文本
            top_k: 返回的最相关结果数量
            filter_conditions: 可选的元数据过滤条件

        返回:
            按相关性降序排列的 SearchResult 列表
        """
        ...
