"""文档处理管道 — DocumentPipeline

将 Parser → Splitter → Embedding → VectorStore 四个步骤编排为
一个完整的文档处理流水线。Pipeline 只负责编排，不包含任何实现细节。

用法::

    from app.rag.parsers import ParserRouter, register_default_parsers
    from app.rag.splitters import FixedSizeSplitter
    from app.rag.embeddings import BGESmallEmbedding
    from app.rag.vector_stores import ChromaDBStore
    from app.rag.pipeline import DocumentPipeline

    router = ParserRouter()
    register_default_parsers(router)

    pipeline = DocumentPipeline(
        parser_router=router,
        splitter=FixedSizeSplitter(chunk_size=512),
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
from typing import List

from app.rag.interfaces.parser import ParsedDocument, DocumentParser
from app.rag.interfaces.splitter import TextSplitter, DocumentChunk
from app.rag.interfaces.embedding import EmbeddingBackend
from app.rag.interfaces.vector_store import VectorStore
from app.rag.parsers.parser_router import ParserRouter


class DocumentPipeline:
    """文档处理管道

    将文档从原始文件处理为向量并存入向量数据库的完整编排流程。

    参数:
        parser_router: 文档解析器路由，负责根据扩展名选择解析器
        splitter: 文本切片器，将文档切分为可检索的片段
        embedding: Embedding 后端，将文本转为向量
        vector_store: 向量存储后端，保存向量及其元数据
    """

    def __init__(
        self,
        parser_router: ParserRouter,
        splitter: TextSplitter,
        embedding: EmbeddingBackend,
        vector_store: VectorStore,
    ):
        self._parser_router = parser_router
        self._splitter = splitter
        self._embedding = embedding
        self._vector_store = vector_store

    def process_document(
        self,
        file_path: str,
        document_id: str,
        user_id: str,
        dataset_id: str,
    ) -> int:
        """处理单个文档：解析 → 切片 → Embedding → 存储

        执行流程:
            Step 1: 根据文件扩展名获取解析器
            Step 2: ``parser.parse(file_path)`` → 结构化文档
            Step 3: ``splitter.split(content, metadata)`` → 切片列表
            Step 4: ``embedding.embed_documents(texts)`` → 向量列表
            Step 5: ``vector_store.add_embeddings(ids, vectors, metadatas)``
            Step 6: 返回切片数量

        参数:
            file_path: 文档的完整路径
            document_id: 文档唯一标识
            user_id: 所属用户 ID
            dataset_id: 所属数据集 ID

        返回:
            生成的切片数量

        异常:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
            ParseError: 解析过程出错
            RuntimeError: 向量存储失败
        """
        # === Step 1: 获取解析器 ===
        ext = os.path.splitext(file_path)[1].lower()
        parser: DocumentParser = self._parser_router.get_parser(ext)
        if parser is None:
            raise ValueError(
                f"不支持的文件格式 '{ext}'，支持的格式: "
                f"{', '.join(self._parser_router.get_supported_extensions())}"
            )

        # === Step 2: 解析文档 ===
        parsed: ParsedDocument = parser.parse(file_path)

        # 空文档快速返回
        if not parsed.content.strip():
            return 0

        # === Step 3: 切片 ===
        # 构建文档级元数据，传递给 splitter 合并到每个 chunk
        doc_metadata = {
            "document_id": document_id,
            "user_id": user_id,
            "dataset_id": dataset_id,
            "source": file_path,
        }
        # 合并解析器提取的元数据（如 title, author, total_pages）
        doc_metadata.update(parsed.metadata)

        chunks: List[DocumentChunk] = self._splitter.split(
            parsed.content,
            metadata=doc_metadata,
        )

        if not chunks:
            return 0

        # === Step 4: Embedding ===
        texts = [chunk.content for chunk in chunks]
        vectors = self._embedding.embed_documents(texts)

        # === Step 5: 构建 IDs 和 metadatas 并存储 ===
        ids: List[str] = []
        metadatas: List[dict] = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_{chunk.chunk_index}"
            ids.append(chunk_id)

            # 合并 chunk 级别的元数据
            chunk_metadata = dict(chunk.metadata)
            chunk_metadata["chunk_index"] = chunk.chunk_index
            metadatas.append(chunk_metadata)

        self._vector_store.add_embeddings(
            ids=ids,
            vectors=vectors,
            metadatas=metadatas,
        )

        # === Step 6: 返回切片数量 ===
        return len(chunks)

    @property
    def parser_router(self) -> ParserRouter:
        """返回当前使用的解析器路由实例"""
        return self._parser_router

    @property
    def splitter(self) -> TextSplitter:
        """返回当前使用的切片器实例"""
        return self._splitter

    @property
    def embedding(self) -> EmbeddingBackend:
        """返回当前使用的 Embedding 后端实例"""
        return self._embedding

    @property
    def vector_store(self) -> VectorStore:
        """返回当前使用的向量存储实例"""
        return self._vector_store
