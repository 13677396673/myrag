"""BGE 本地 Embedding 模型实现

使用 ``sentence-transformers`` 加载 BAAI/bge-small-zh-v1.5 模型
并在本地 CPU/GPU 上计算文本向量。

用法::

    from app.rag.embeddings import BGESmallEmbedding

    emb = BGESmallEmbedding()
    await emb.load()            # 异步加载模型（首次会下载）
    vec = emb.embed_text("你好世界")
    print(emb.dimension)  # 384
"""

import asyncio
from typing import List

from app.rag.interfaces.embedding import EmbeddingBackend


class BGESmallEmbedding(EmbeddingBackend):
    """BAAI/bge-small-zh-v1.5 本地模型 Embedding 实现

    基于 ``sentence-transformers`` 库加载本地模型，不依赖外部 API。
    默认在 CPU 上运行，可通过 ``device="cuda"`` 启用 GPU。

    ``__init__`` 仅保存参数，**不加载模型**；需要先调用 ``async load()``
    才能使用 ``embed_text`` / ``embed_documents``。

    参数:
        model_name: HuggingFace 模型名称，默认 ``BAAI/bge-small-zh-v1.5``
        device: 运行设备，``"cpu"`` 或 ``"cuda"``
    """

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5", device: str = "cpu"):
        self._model_name = model_name
        self._device = device
        self._model = None

    async def load(self) -> None:
        """异步加载 SentenceTransformer 模型

        在后台线程池中执行模型加载，避免阻塞事件循环。
        首次调用会从 HuggingFace Hub 下载模型（缓存到本地后后续加载更快）。

        用法::

            emb = BGESmallEmbedding()
            await emb.load()
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model)

    def _load_model(self) -> None:
        """同步加载 ``SentenceTransformer`` 模型（在后台线程中执行）

        调用 ``sentence_transformers.SentenceTransformer`` 从 HuggingFace Hub
        下载（首次）并加载模型到指定设备。
        """
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self._model_name, device=self._device)

    def _check_loaded(self) -> None:
        """检查模型是否已加载，未加载则抛出 RuntimeError"""
        if self._model is None:
            raise RuntimeError(
                "BGESmallEmbedding 模型尚未加载，请先调用 await load()"
            )

    def embed_text(self, text: str) -> List[float]:
        """将单条文本转为 384 维向量

        参数:
            text: 输入文本

        返回:
            长度为 384 的浮点数向量

        异常:
            RuntimeError: 模型尚未加载
        """
        self._check_loaded()
        return self._model.encode(text).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转为向量

        参数:
            texts: 输入文本列表

        返回:
            与输入顺序一致的向量列表，每个向量长度为 384

        异常:
            RuntimeError: 模型尚未加载
        """
        self._check_loaded()
        embeddings = self._model.encode(texts, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    @property
    def dimension(self) -> int:
        """返回向量维度

        bge-small-zh 固定输出 384 维向量。
        """
        return 384
