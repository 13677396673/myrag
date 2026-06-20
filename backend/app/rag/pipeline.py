"""文档处理管道 — DocumentPipeline

将 Parser → Splitter → Embedding → VectorStore 四个步骤编排为
一个完整的文档处理流水线。Pipeline 只负责编排，不包含任何实现细节。

Pipeline 不再直接持有单一的 ParserRouter 和 Splitter，而是通过
``StrategyRouter`` 根据文档类型自动选择对应的 (parser, splitter) 配对
进行结构感知的切分。

用法::

    from app.rag.strategies import StrategyRouter, register_default_strategies
    from app.rag.embeddings import BGESmallEmbedding
    from app.rag.vector_stores import ChromaDBStore
    from app.rag.pipeline import DocumentPipeline

    router = StrategyRouter()
    register_default_strategies(router)

    pipeline = DocumentPipeline(
        strategy_router=router,
        embedding=BGESmallEmbedding(),
        vector_store=ChromaDBStore(persist_directory="./data/chromadb"),
    )

    chunk_count = pipeline.process_document(
        file_path="/path/to/doc.pdf",
        document_id="doc-001",
        user_id="user-1",
        dataset_id="ds-001",
    )
    print(f"已处理 {chunk_count} 个切片")
"""

import os
from typing import List, Optional

from app.rag.interfaces.parser import ParsedDocument, DocumentParser
from app.rag.interfaces.splitter import TextSplitter, DocumentChunk
from app.rag.interfaces.embedding import EmbeddingBackend
from app.rag.interfaces.vector_store import VectorStore
from app.rag.strategies import StrategyRouter, ChunkingStrategy


class DocumentPipeline:
    """文档处理管道

    将文档从原始文件处理为向量并存入向量数据库的完整编排流程。

    通过 ``StrategyRouter`` 根据文档扩展名自动选择合适的
    (parser, splitter) 配对，实现结构感知的智能切分。

    参数:
        strategy_router: 文档 chunking 策略路由，根据扩展名选择策略
        embedding: Embedding 后端，将文本转为向量
        vector_store: 向量存储后端，保存向量及其元数据
    """

    def __init__(
        self,
        strategy_router: StrategyRouter,
        embedding: EmbeddingBackend,
        vector_store: VectorStore,
    ):
        self._strategy_router = strategy_router
        self._embedding = embedding
        self._vector_store = vector_store
        # 最后一次 process_document 的切片数据，供外部保存到 SQL
        self.last_chunks: List[DocumentChunk] = []

    def process_document(
        self,
        file_path: str,
        document_id: str,
        user_id: str,
        dataset_id: str,
        filename: Optional[str] = None,
    ) -> int:
        """处理单个文档：解析 → 切片 → Embedding → 存储

        执行流程:
            Step 1: 根据文件扩展名获取 chunking 策略
            Step 2: ``strategy.execute(file_path)`` → 解析 + 切片
            Step 3: ``embedding.embed_documents(texts)`` → 向量列表
            Step 4: ``vector_store.add_embeddings(ids, vectors, metadatas, documents)``
            Step 5: 返回切片数量

        参数:
            file_path: 文档的完整路径
            document_id: 文档唯一标识
            user_id: 所属用户 ID
            dataset_id: 所属数据集 ID
            filename: 原始文件名（显示用），不传则从 file_path 提取 basename

        返回:
            生成的切片数量

        异常:
            ValueError: 不支持的文件格式
            ParseError: 解析过程出错
            RuntimeError: 向量存储失败
        """
        # === Step 1: 获取策略 ===
        ext = os.path.splitext(file_path)[1].lower()
        strategy: Optional[ChunkingStrategy] = self._strategy_router.get_strategy(ext)
        if strategy is None:
            raise ValueError(
                f"不支持的文件格式 '{ext}'，支持的格式: "
                f"{', '.join(self._strategy_router.get_supported_extensions())}"
            )

        # === Step 2: 执行策略（解析 + 切片） ===
        # 构建文档级元数据，传递给策略合并到每个 chunk
        doc_metadata = {
            "document_id": document_id,
            "user_id": user_id,
            "dataset_id": dataset_id,
            "source": file_path,
            "document_name": filename or os.path.basename(file_path),
        }

        chunks = strategy.execute(file_path, metadata=doc_metadata)

        if not chunks:
            self.last_chunks = []
            return 0

        # === Step 3: Embedding ===
        texts = [chunk.content for chunk in chunks]
        vectors = self._embedding.embed_documents(texts)

        # === Step 4: 构建 IDs 和 metadatas 并存储 ===
        ids: List[str] = []
        metadatas: List[dict] = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_{chunk.chunk_index}"
            ids.append(chunk_id)

            # 合并 chunk 级别的元数据
            chunk_metadata = dict(chunk.metadata)
            chunk_metadata["chunk_index"] = chunk.chunk_index
            chunk_metadata["content"] = chunk.content  # 文本内容也存到 metadata
            metadatas.append(chunk_metadata)

        self._vector_store.add_embeddings(
            ids=ids,
            vectors=vectors,
            metadatas=metadatas,
            documents=texts,
        )

        # 保留切片数据，供外部保存到 SQL Chunk 表
        self.last_chunks = chunks

        # === Step 5: 返回切片数量 ===
        return len(chunks)

    # ── 属性（兼容旧接口的部分访问） ──

    @property
    def strategy_router(self) -> StrategyRouter:
        """返回当前使用的策略路由实例"""
        return self._strategy_router

    @property
    def embedding(self) -> EmbeddingBackend:
        """返回当前使用的 Embedding 后端实例"""
        return self._embedding

    @property
    def vector_store(self) -> VectorStore:
        """返回当前使用的向量存储实例"""
        return self._vector_store
