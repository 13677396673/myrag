"""Embedding 模块

提供 ``BGESmallEmbedding``（本地 BGE 模型）和 ``OpenAIEmbedding``（OpenAI API）
两种 Embedding 实现，以及 ``create_embedding`` 工厂函数用于根据配置自动选择。

用法::

    from app.config import settings
    from app.rag.embeddings import create_embedding

    embedding = create_embedding(settings)

    # 或直接实例化
    from app.rag.embeddings import BGESmallEmbedding
    emb = BGESmallEmbedding()
    vec = emb.embed_text("你好世界")
"""

from .bge_embedding import BGESmallEmbedding
from .openai_embedding import OpenAIEmbedding
from .deepseek_embedding import DeepSeekEmbedding

__all__ = [
    "BGESmallEmbedding",
    "OpenAIEmbedding",
    "DeepSeekEmbedding",
    "create_embedding",
]


def create_embedding(settings) -> "BGESmallEmbedding | OpenAIEmbedding":
    """根据配置创建 Embedding 后端实例

    依据 ``settings.EMBEDDING_BACKEND`` 的值选择实现：

    - ``bge-small`` → 创建 ``BGESmallEmbedding``
    - ``openai`` → 创建 ``OpenAIEmbedding``
    - ``deepseek`` → 使用 OpenAI 兼容客户端创建 DeepSeek Embedding

    参数:
        settings: 应用配置对象（``app.config.Settings``）

    返回:
        实现了 ``EmbeddingBackend`` 接口的实例

    异常:
        ValueError: 不支持的 ``EMBEDDING_BACKEND`` 值
    """
    backend = settings.EMBEDDING_BACKEND

    if backend == "bge-small":
        return BGESmallEmbedding(
            model_name=settings.EMBEDDING_BGE_MODEL,
            device=settings.EMBEDDING_BGE_DEVICE,
        )

    if backend == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置，无法创建 OpenAIEmbedding")
        return OpenAIEmbedding(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_OPENAI_MODEL,
        )

    if backend == "deepseek":
        if not settings.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY 未配置，无法创建 DeepSeek Embedding")
        return DeepSeekEmbedding(
            api_key=settings.DEEPSEEK_API_KEY,
            model=settings.EMBEDDING_DEEPSEEK_MODEL,
            base_url=settings.DEEPSEEK_BASE_URL,
        )

    msg = f"不支持的 EMBEDDING_BACKEND: {backend!r}，可选值: bge-small, openai, deepseek"
    raise ValueError(msg)
