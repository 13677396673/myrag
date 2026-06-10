"""pytest fixtures for DocumentPipeline tests

提供模拟的 ParserRouter、TextSplitter、EmbeddingBackend、VectorStore
以及完整的 DocumentPipeline 实例。
"""

from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from app.rag.interfaces.parser import ParsedDocument, DocumentParser
from app.rag.interfaces.splitter import TextSplitter, DocumentChunk
from app.rag.interfaces.embedding import EmbeddingBackend
from app.rag.interfaces.vector_store import VectorStore, SearchResult
from app.rag.parsers.parser_router import ParserRouter
from app.rag.pipeline import DocumentPipeline


# =========================================================================
# Mock implementations
# =========================================================================


class MockParser(DocumentParser):
    """模拟解析器：解析后返回固定内容"""

    def __init__(self, content: str = "模拟文档内容", metadata: Optional[dict] = None):
        self._content = content
        self._metadata = metadata or {}

    def parse(self, file_path: str) -> ParsedDocument:
        return ParsedDocument(content=self._content, metadata=self._metadata)

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return [".txt", ".md"]


class MockSplitter(TextSplitter):
    """模拟切片器：返回固定数量的切片"""

    def __init__(self, chunk_count: int = 3):
        self._chunk_count = chunk_count
        self.last_text = None
        self.last_metadata = None

    def split(self, text: str, metadata: Optional[dict] = None) -> List[DocumentChunk]:
        self.last_text = text
        self.last_metadata = metadata
        return [
            DocumentChunk(
                content=f"切片 {i} 内容",
                chunk_index=i,
                metadata=dict(metadata or {}) if metadata else {},
            )
            for i in range(self._chunk_count)
        ]

    @property
    def type_name(self) -> str:
        return "mock"


class MockEmbedding(EmbeddingBackend):
    """模拟 Embedding：返回固定维度的向量"""

    def __init__(self, dimension: int = 4):
        self._dimension = dimension
        self.last_texts = None

    def embed_text(self, text: str) -> List[float]:
        return [0.1] * self._dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self.last_texts = texts
        return [[0.1] * self._dimension for _ in texts]

    @property
    def dimension(self) -> int:
        return self._dimension


class MockVectorStore(VectorStore):
    """模拟向量存储：记录调用参数但不实际存储"""

    def __init__(self):
        self.added_ids = None
        self.added_vectors = None
        self.added_metadatas = None

    def add_embeddings(self, ids, vectors, metadatas):
        self.added_ids = ids
        self.added_vectors = vectors
        self.added_metadatas = metadatas

    def search(self, query_vector, top_k=5, filter_conditions=None):
        return []

    def delete(self, ids):
        pass

    def delete_by_metadata(self, filter_conditions):
        return 0

    def count(self, filter_conditions=None):
        return 0


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def mock_parser():
    """返回一个模拟解析器（解析后返回 "模拟文档内容"）"""
    return MockParser(content="这是模拟的文档内容")


@pytest.fixture
def mock_parser_empty():
    """返回一个解析空文档的模拟解析器"""
    return MockParser(content="   ")


@pytest.fixture
def mock_splitter():
    """返回一个生成 3 个切片的模拟切片器"""
    return MockSplitter(chunk_count=3)


@pytest.fixture
def mock_splitter_empty():
    """返回一个生成 0 个切片的模拟切片器"""
    return MockSplitter(chunk_count=0)


@pytest.fixture
def mock_embedding():
    """返回一个 4 维向量的模拟 Embedding"""
    return MockEmbedding(dimension=4)


@pytest.fixture
def mock_vector_store():
    """返回一个模拟向量存储"""
    return MockVectorStore()


@pytest.fixture
def parser_router(mock_parser):
    """返回一个注册了 MockParser 的 ParserRouter"""
    router = ParserRouter()
    router.register(MockParser)
    return router


@pytest.fixture
def pipeline(parser_router, mock_splitter, mock_embedding, mock_vector_store):
    """返回一个完整的 DocumentPipeline 实例（所有组件均为 Mock）"""
    return DocumentPipeline(
        parser_router=parser_router,
        splitter=mock_splitter,
        embedding=mock_embedding,
        vector_store=mock_vector_store,
    )
