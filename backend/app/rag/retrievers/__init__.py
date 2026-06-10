"""检索器模块

提供 ``VectorRetriever``（向量检索器）实现，
以及 HybridRetriever / BM25Retriever 占位类供后续扩展。

用法::

    from app.config import settings
    from app.rag.retrievers import create_retriever

    retriever = create_retriever(settings)
    results = retriever.retrieve("什么是 RAG？", top_k=5)

或直接实例化::

    from app.rag.retrievers import VectorRetriever

    retriever = VectorRetriever(embedding=emb, vector_store=store)
    results = retriever.retrieve("什么是 RAG？")
"""

from .vector_retriever import VectorRetriever

__all__ = [
    "VectorRetriever",
    "create_retriever",
]


def create_retriever(settings, embedding, vector_store) -> "VectorRetriever":
    """根据配置创建检索器实例

    依据 ``settings.RETRIEVAL_MODE`` 的值选择实现：

    - ``vector`` → 创建 ``VectorRetriever``
    - ``hybrid`` → 抛出 ``ValueError``（尚未实现）

    参数:
        settings: 应用配置对象（``app.config.Settings``）
        embedding: 实现了 ``EmbeddingBackend`` 接口的实例
        vector_store: 实现了 ``VectorStore`` 接口的实例

    返回:
        实现了 ``Retriever`` 接口的实例

    异常:
        ValueError: 不支持的 ``RETRIEVAL_MODE`` 值或未实现的占位后端
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
        raise ValueError("混合检索尚未实现（预留中）")

    msg = f"不支持的 RETRIEVAL_MODE: {mode!r}，可选值: vector, hybrid"
    raise ValueError(msg)
