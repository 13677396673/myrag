"""向量检索器实现

``VectorRetriever`` 将 ``EmbeddingBackend`` 和 ``VectorStore``
通过"编排"的方式组合起来：先用 Embedding 将查询转为向量，
再用该向量在 VectorStore 中执行相似性搜索。

这是一个纯编排层，不包含业务逻辑，所有 filter_conditions
由上层 Service 拼接后传入。

用法::

    from app.rag.embeddings import BGESmallEmbedding
    from app.rag.vector_stores import ChromaDBStore
    from app.rag.retrievers import VectorRetriever

    emb = BGESmallEmbedding()
    store = ChromaDBStore()
    retriever = VectorRetriever(embedding=emb, vector_store=store)

    results = retriever.retrieve("什么是 RAG？", top_k=5)
"""

from typing import List, Optional

from app.rag.interfaces.retriever import Retriever
from app.rag.interfaces.embedding import EmbeddingBackend
from app.rag.interfaces.vector_store import VectorStore, SearchResult


class VectorRetriever(Retriever):
    """向量检索器

    将查询文本转为向量后在向量数据库中执行相似性搜索。

    参数:
        embedding: 实现了 ``EmbeddingBackend`` 接口的嵌入模型实例
        vector_store: 实现了 ``VectorStore`` 接口的向量存储实例
        top_k: 默认检索数量（可在 ``retrieve`` 调用时覆盖）
        similarity_threshold: 相似度阈值，低于此值的结果将被过滤掉（0.0 表示不过滤）
    """

    def __init__(
        self,
        embedding: EmbeddingBackend,
        vector_store: VectorStore,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
    ):
        self._embedding = embedding
        self._vector_store = vector_store
        self._default_top_k = top_k
        self._similarity_threshold = similarity_threshold

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_conditions: Optional[dict] = None,
    ) -> List[SearchResult]:
        """根据查询文本检索相关文档片段

        执行流程：
        1. 调用 ``EmbeddingBackend.embed_text(query)`` 将查询转为向量
        2. 调用 ``VectorStore.search(query_vector, top_k, filter_conditions)``
        3. 根据 ``similarity_threshold`` 过滤低分结果
        4. 返回按相关性降序排列的 ``SearchResult`` 列表

        参数:
            query: 用户查询文本
            top_k: 返回的最相关结果数量
            filter_conditions: 可选的元数据过滤条件，如 ``{"dataset_id": "xxx"}``

        返回:
            按相关性降序排列的 SearchResult 列表
        """
        # 1. Embedding：文本 → 向量
        query_vector = self._embedding.embed_text(query)

        # 2. 向量检索
        results = self._vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            filter_conditions=filter_conditions,
        )

        # 3. 相似度阈值过滤
        if self._similarity_threshold > 0.0:
            results = [
                r for r in results
                if r.score >= self._similarity_threshold
            ]

        return results

    @property
    def embedding(self) -> EmbeddingBackend:
        """返回当前使用的 Embedding 后端实例"""
        return self._embedding

    @property
    def vector_store(self) -> VectorStore:
        """返回当前使用的向量存储实例"""
        return self._vector_store
