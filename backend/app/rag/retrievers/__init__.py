"""检索器模块

提供 ``VectorRetriever``（向量检索）、``BM25Retriever``（关键词检索）、
``HybridRetriever``（向量 + BM25 RRF 融合）三种检索器实现。

使用 ``create_retriever(settings, embedding, vector_store)`` 工厂函数
根据应用配置（``settings.RETRIEVAL_MODE``）自动创建对应的实例。

用法::

    from app.config import settings
    from app.rag.retrievers import create_retriever

    retriever = create_retriever(settings, embedding, vector_store)
    results = retriever.retrieve("什么是 RAG？", top_k=5)

或直接实例化::

    from app.rag.retrievers import VectorRetriever, BM25Retriever, HybridRetriever

    vector = VectorRetriever(embedding=emb, vector_store=store)
    bm25 = BM25Retriever(vector_store=store)
    hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
    results = hybrid.retrieve("什么是 RAG？")
"""

from .bm25_retriever import BM25Retriever
from .vector_retriever import VectorRetriever
from .hybrid_retriever import HybridRetriever

__all__ = [
    "VectorRetriever",
    "BM25Retriever",
    "HybridRetriever",
    "create_retriever",
]


def create_retriever(settings, embedding, vector_store) -> "VectorRetriever | HybridRetriever":
    """根据配置创建检索器实例

    依据 ``settings.RETRIEVAL_MODE`` 的值选择实现：

    - ``vector`` → 创建 ``VectorRetriever``（纯语义检索）
    - ``hybrid`` → 创建 ``HybridRetriever``（语义 + 关键词 RRF 融合），
      内部会自动创建 ``VectorRetriever`` 和 ``BM25Retriever`` 子实例

    参数:
        settings: 应用配置对象（``app.config.Settings``）
        embedding: 实现了 ``EmbeddingBackend`` 接口的实例
        vector_store: 实现了 ``VectorStore`` 接口的实例

    返回:
        实现了 ``Retriever`` 接口的实例

    异常:
        ValueError: 不支持的 ``RETRIEVAL_MODE`` 值
    """
    mode = settings.RETRIEVAL_MODE

    if mode == "vector":
        return VectorRetriever(
            embedding=embedding,
            vector_store=vector_store,
            top_k=settings.RETRIEVAL_TOP_K,
            similarity_threshold=settings.RETRIEVAL_SIMILARITY_THRESHOLD,
        )

    if mode == "hybrid":
        vector_retriever = VectorRetriever(
            embedding=embedding,
            vector_store=vector_store,
            top_k=settings.RETRIEVAL_TOP_K,
            similarity_threshold=settings.RETRIEVAL_SIMILARITY_THRESHOLD,
        )
        bm25_retriever = BM25Retriever(
            vector_store=vector_store,
            top_k=settings.RETRIEVAL_TOP_K,
        )
        return HybridRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            top_k=settings.RETRIEVAL_TOP_K,
        )

    msg = f"不支持的 RETRIEVAL_MODE: {mode!r}，可选值: vector, hybrid"
    raise ValueError(msg)
