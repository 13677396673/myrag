"""ChromaDB 向量存储实现

使用 ChromaDB 嵌入式向量数据库作为本地持久化后端，
支持 Cosine 距离搜索、元数据过滤、CRUD 操作。

用法::

    from app.rag.vector_stores import ChromaDBStore

    store = ChromaDBStore(persist_directory="./data/chromadb")
    store.add_embeddings(
        ids=["chunk_1"],
        vectors=[[0.1, 0.2, ...]],
        metadatas=[{"dataset_id": "ds1", "user_id": "u1"}],
    )
    results = store.search(query_vector=[...], top_k=5)
"""

from typing import List, Optional, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.rag.interfaces.vector_store import VectorStore, SearchResult, Document


class ChromaDBStore(VectorStore):
    """ChromaDB 向量存储实现

    基于 ChromaDB 的 ``PersistentClient``，数据持久化到本地磁盘。
    使用 Cosine 距离（HNSW 索引）进行相似度搜索。

    参数:
        persist_directory: 数据持久化目录
        collection_name: 集合名称，默认 ``"documents"``
    """

    def __init__(
        self,
        persist_directory: str = "./data/chromadb",
        collection_name: str = "documents",
    ):
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_embeddings(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: Optional[List[str]] = None,
    ) -> None:
        """添加向量及其元数据

        ChromaDB 要求 metadata 的值必须为基本类型（str / int / float / bool），
        因此会自动将 dict 和 list 类型的值转为字符串。

        参数:
            ids: 向量 ID 列表
            vectors: 向量数据列表
            metadatas: 元数据字典列表
            documents: 可选的原始文本列表，与 ids/vectors 一一对应
        """
        sanitized = []
        for m in metadatas:
            sanitized.append({
                k: (str(v) if isinstance(v, (dict, list)) else v)
                for k, v in m.items()
            })
        kwargs: Dict[str, Any] = {
            "ids": ids,
            "embeddings": vectors,
            "metadatas": sanitized,
        }
        if documents is not None:
            kwargs["documents"] = documents
        self._collection.add(**kwargs)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """搜索与查询向量最相似的 top_k 个结果

        参数:
            query_vector: 查询向量
            top_k: 返回的最相似结果数量
            filter_conditions: 元数据过滤条件

        返回:
            按距离升序（相似度降序）排列的 SearchResult 列表
        """
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=filter_conditions,
        )
        if not results["ids"] or not results["ids"][0]:
            return []

        items = []
        for i in range(len(results["ids"][0])):
            items.append(SearchResult(
                id=results["ids"][0][i],
                content=results["documents"][0][i] if results.get("documents") else None,
                score=results["distances"][0][i] if results.get("distances") else 0.0,
                metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
            ))
        return items

    def delete(self, ids: List[str]) -> None:
        """按 ID 列表删除向量

        参数:
            ids: 要删除的向量 ID 列表；不存在的 ID 会被静默忽略
        """
        self._collection.delete(ids=ids)

    def delete_by_metadata(self, filter_conditions: Dict[str, Any]) -> int:
        """按元数据条件删除，返回删除的数量

        ChromaDB 不直接支持按 metadata 删除，需要先查再删。

        参数:
            filter_conditions: 过滤条件字典

        返回:
            实际删除的向量数量
        """
        results = self._collection.get(where=filter_conditions)
        ids = results.get("ids", [])
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    def count(self, filter_conditions: Optional[Dict[str, Any]] = None) -> int:
        """返回匹配的向量数量

        参数:
            filter_conditions: 可选的过滤条件；为 ``None`` 时返回总数

        返回:
            匹配的向量数量
        """
        if filter_conditions is None:
            return self._collection.count()

        results = self._collection.get(where=filter_conditions)
        return len(results.get("ids", []))

    def get_all(
        self,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """获取所有文档（不含向量）

        参数:
            filter_conditions: 可选的元数据过滤条件

        返回:
            Document 列表
        """
        kwargs: Dict[str, Any] = {}
        if filter_conditions:
            kwargs["where"] = filter_conditions
        results = self._collection.get(**kwargs)
        if not results["ids"]:
            return []

        docs = []
        for i in range(len(results["ids"])):
            docs.append(Document(
                id=results["ids"][i],
                content=results["documents"][i] if results.get("documents") else "",
                metadata=results["metadatas"][i] if results.get("metadatas") else {},
            ))
        return docs
