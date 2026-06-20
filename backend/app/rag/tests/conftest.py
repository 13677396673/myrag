"""pytest fixtures for DocumentPipeline tests

提供模拟的 StrategyRouter、ChunkingStrategy、TextSplitter、EmbeddingBackend、
VectorStore 以及完整的 DocumentPipeline 实例。
"""

from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from app.rag.interfaces.parser import ParsedDocument, DocumentParser
from app.rag.interfaces.splitter import TextSplitter, DocumentChunk
from app.rag.interfaces.embedding import EmbeddingBackend
from app.rag.interfaces.vector_store import VectorStore, SearchResult
from app.rag.interfaces.llm import LLMBackend
from app.rag.interfaces.retriever import Retriever
from app.rag.strategies import StrategyRouter, ChunkingStrategy
from app.rag.pipeline import DocumentPipeline


# =========================================================================
# Mock implementations
# =========================================================================


class MockParser(DocumentParser):
    """模拟解析器：解析后返回固定内容"""

    def __init__(self, content: str = "模拟文档内容", metadata: Optional[dict] = None, sections: Optional[List[dict]] = None):
        self._content = content
        self._metadata = metadata or {}
        self._sections = sections or []

    def parse(self, file_path: str) -> ParsedDocument:
        return ParsedDocument(content=self._content, metadata=self._metadata, sections=self._sections)

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return [".txt", ".md", ".pdf", ".docx"]


class MockSplitter(TextSplitter):
    """模拟切片器：返回固定数量的切片"""

    def __init__(self, chunk_count: int = 3):
        self._chunk_count = chunk_count
        self.last_text = None
        self.last_metadata = None
        self.last_sections = None

    def split(self, text: str, metadata: Optional[dict] = None, sections: Optional[List[dict]] = None) -> List[DocumentChunk]:
        self.last_text = text
        self.last_metadata = metadata
        self.last_sections = sections
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

    def add_embeddings(self, ids, vectors, metadatas, documents=None):
        self.added_ids = ids
        self.added_vectors = vectors
        self.added_metadatas = metadatas
        self.added_documents = documents

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
def strategy_router(mock_parser, mock_splitter):
    """返回一个注册了 MockParser + MockSplitter 的 StrategyRouter

    对 .txt / .md / .pdf / .docx 都注册同一个 mock 策略，
    确保测试中所有扩展名都能被路由。
    """
    router = StrategyRouter()
    strategy = ChunkingStrategy(
        name="mock",
        parser=mock_parser,
        splitter=mock_splitter,
        description="Mock 测试策略",
    )
    router.register([".txt", ".md", ".pdf", ".docx"], strategy)
    return router


@pytest.fixture
def pipeline(strategy_router, mock_embedding, mock_vector_store):
    """返回一个完整的 DocumentPipeline 实例（使用 mock 策略路由）"""
    return DocumentPipeline(
        strategy_router=strategy_router,
        embedding=mock_embedding,
        vector_store=mock_vector_store,
    )


# =========================================================================
# RAGEngine Mocks & Fixtures
# =========================================================================


class MockRetriever(Retriever):
    """模拟检索器：返回固定的检索结果"""

    def __init__(self, results: Optional[List[SearchResult]] = None):
        self._results = results or []
        self.last_query = None
        self.last_top_k = None
        self.last_filter_conditions = None

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_conditions: Optional[dict] = None,
    ) -> List[SearchResult]:
        self.last_query = query
        self.last_top_k = top_k
        self.last_filter_conditions = filter_conditions
        return self._results


class MockLLM(LLMBackend):
    """模拟 LLM 后端：支持非流式和流式生成"""

    def __init__(
        self,
        response: str = "这是基于检索结果的回答。",
        tokens: Optional[List[str]] = None,
        model_name: str = "mock-model",
    ):
        self._response = response
        self._tokens = tokens or list(response)
        self._model_name = model_name
        self.last_messages = None
        self.last_temperature = None
        self.last_max_tokens = None

    async def generate(
        self,
        messages,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        self.last_messages = messages
        self.last_temperature = temperature
        self.last_max_tokens = max_tokens
        return self._response

    async def generate_stream(self, messages, temperature=0.7, max_tokens=2048):
        self.last_messages = messages
        self.last_temperature = temperature
        self.last_max_tokens = max_tokens
        for token in self._tokens:
            yield token

    @property
    def model_name(self) -> str:
        return self._model_name


# ── RAGEngine Fixtures ──


@pytest.fixture
def mock_retriever():
    """返回一个无结果的模拟检索器"""
    return MockRetriever(results=[])


@pytest.fixture
def mock_retriever_with_results():
    """返回一个有 3 条检索结果的模拟检索器"""
    results = [
        SearchResult(
            id="chunk-001",
            score=0.95,
            metadata={"document_id": "doc-1", "chunk_index": 0},
            content="RAG 是检索增强生成的缩写。",
        ),
        SearchResult(
            id="chunk-002",
            score=0.88,
            metadata={"document_id": "doc-1", "chunk_index": 1},
            content="RAG 结合了检索和生成两种技术。",
        ),
        SearchResult(
            id="chunk-003",
            score=0.72,
            metadata={"document_id": "doc-2", "chunk_index": 0},
            content="检索增强生成能有效减少模型幻觉。",
        ),
    ]
    return MockRetriever(results=results)


@pytest.fixture
def mock_llm():
    """返回一个模拟 LLM 后端"""
    return MockLLM(response="这是基于检索结果的回答。")


@pytest.fixture
def rag_engine(mock_retriever_with_results, mock_llm):
    """返回一个完整的 RAGEngine 实例（所有组件均为 Mock）"""
    from app.rag.rag_engine import RAGEngine

    return RAGEngine(retriever=mock_retriever_with_results, llm=mock_llm)
