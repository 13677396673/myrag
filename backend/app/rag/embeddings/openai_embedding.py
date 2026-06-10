"""OpenAI Embedding API 实现

通过 OpenAI API 调用 ``text-embedding-3-small`` 等模型计算文本向量。

用法::

    from app.rag.embeddings import OpenAIEmbedding

    emb = OpenAIEmbedding(api_key="sk-...")
    vec = emb.embed_text("你好世界")
    print(emb.dimension)  # 1536
"""

from typing import List

from app.rag.interfaces.embedding import EmbeddingBackend


class OpenAIEmbedding(EmbeddingBackend):
    """OpenAI Embedding API 封装

    使用 OpenAI 官方 Python SDK 调用 Embedding API，
    支持 ``text-embedding-3-small``、``text-embedding-3-large`` 等模型。
    批量调用时按输入顺序排序返回结果。

    参数:
        api_key: OpenAI API 密钥
        model: Embedding 模型名称，默认 ``text-embedding-3-small``
    """

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed_text(self, text: str) -> List[float]:
        """将单条文本转为向量

        参数:
            text: 输入文本

        返回:
            浮点数向量列表（text-embedding-3-small 为 1536 维）
        """
        resp = self._client.embeddings.create(input=text, model=self._model)
        return resp.data[0].embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转为向量

        通过一次 API 调用同时处理多条文本，并按输入顺序排序返回结果。

        参数:
            texts: 输入文本列表

        返回:
            与输入顺序一致的向量列表
        """
        resp = self._client.embeddings.create(input=texts, model=self._model)
        # API 返回顺序可能乱序，按 index 排序确保与输入一致
        sorted_data = sorted(resp.data, key=lambda x: x.index)
        return [d.embedding for d in sorted_data]

    @property
    def dimension(self) -> int:
        """返回向量维度

        text-embedding-3-small 输出 1536 维向量。
        """
        return 1536
