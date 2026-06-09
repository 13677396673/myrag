from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class SearchResult:
    """向量检索结果"""
    id: str                          # chunk_id
    score: float                     # 相似度得分
    metadata: Dict[str, Any]         # chunk 元数据
    content: Optional[str] = None    # 文本内容（检索时可选返回）


class VectorStore(ABC):
    """向量数据库抽象接口"""

    @abstractmethod
    def add_embeddings(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        添加向量及其元数据到存储。

        参数:
            ids: 向量 ID 列表
            vectors: 向量数据列表
            metadatas: 元数据字典列表，与 ids/vectors 一一对应
        """
        ...

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        搜索与查询向量最相似的 top_k 个结果。

        参数:
            query_vector: 查询向量
            top_k: 返回的最相似结果数量
            filter_conditions: 元数据过滤条件，如 {"user_id": "xxx", "dataset_id": "yyy"}

        返回:
            按相关性降序排列的 SearchResult 列表
        """
        ...

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """按 ID 列表删除向量"""
        ...

    @abstractmethod
    def delete_by_metadata(self, filter_conditions: Dict[str, Any]) -> int:
        """
        按元数据条件删除，返回删除的数量。

        参数:
            filter_conditions: 过滤条件字典

        返回:
            实际删除的向量数量
        """
        ...

    @abstractmethod
    def count(self, filter_conditions: Optional[Dict[str, Any]] = None) -> int:
        """
        返回当前存储的向量数量（可选的过滤条件）。

        参数:
            filter_conditions: 可选的过滤条件

        返回:
            匹配的向量数量
        """
        ...
