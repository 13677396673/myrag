"""DeepSeek Embedding API 实现

DeepSeek 提供与 OpenAI 兼容的 Embedding API，可通过 OpenAI Python SDK 调用。

用法::

    from app.rag.embeddings import DeepSeekEmbedding

    emb = DeepSeekEmbedding(api_key="sk-...")
    vec = emb.embed_text("你好世界")
    print(emb.dimension)  # 1536
"""

from typing import List

from app.rag.interfaces.embedding import EmbeddingBackend


class DeepSeekEmbedding(EmbeddingBackend):
    """DeepSeek Embedding API 封装

    使用 OpenAI 兼容客户端调用 DeepSeek Embedding API。
    默认模型 ``deepseek-embedding``，输出 1536 维向量。

    参数:
        api_key: DeepSeek API 密钥
        model: Embedding 模型名称，默认 ``deepseek-embedding``
        base_url: API 基础地址，默认 ``https://api.deepseek.com``
    """

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-embedding",
        base_url: str = "https://api.deepseek.com",
    ):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def embed_text(self, text: str) -> List[float]:
        """将单条文本转为向量

        参数:
            text: 输入文本

        返回:
            浮点数向量列表（1536 维）
        """
        resp = self._client.embeddings.create(input=text, model=self._model)
        return resp.data[0].embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转为向量

        参数:
            texts: 输入文本列表

        返回:
            与输入顺序一致的向量列表
        """
        resp = self._client.embeddings.create(input=texts, model=self._model)
        sorted_data = sorted(resp.data, key=lambda x: x.index)
        return [d.embedding for d in sorted_data]

    @property
    def dimension(self) -> int:
        """返回向量维度

        deepseek-embedding 输出 1536 维向量。
        """
        return 1536
