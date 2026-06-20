"""
Tests for M08: RAG 抽象接口模块 (rag/interfaces)

验证内容：
1. 所有抽象类不能直接实例化
2. Mock 实现类可以正确调用所有方法
3. dataclass 的默认值
4. 接口方法的参数签名正确
"""

import pytest
from typing import List, AsyncIterator
from dataclasses import fields

from app.rag.interfaces import (
    DocumentParser,
    ParsedDocument,
    TextSplitter,
    DocumentChunk,
    EmbeddingBackend,
    VectorStore,
    SearchResult,
    LLMBackend,
    Retriever,
)


# =========================================================================
# Mock 实现 — 用于验证接口方法签名和调用
# =========================================================================

class MockDocumentParser(DocumentParser):
    """DocumentParser 的 Mock 实现"""

    def parse(self, file_path: str) -> ParsedDocument:
        return ParsedDocument(content="test", metadata={"source": file_path}, sections=[])

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return [".txt", ".md"]


class MockTextSplitter(TextSplitter):
    """TextSplitter 的 Mock 实现"""

    def split(self, text: str, metadata: dict = None, sections: list = None) -> List[DocumentChunk]:
        return [DocumentChunk(content=text, chunk_index=0, metadata=metadata or {})]

    @property
    def type_name(self) -> str:
        return "mock"


class MockEmbeddingBackend(EmbeddingBackend):
    """EmbeddingBackend 的 Mock 实现"""

    def embed_text(self, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    @property
    def dimension(self) -> int:
        return 3


class MockVectorStore(VectorStore):
    """VectorStore 的 Mock 实现"""

    def __init__(self):
        self._data: dict = {}

    def add_embeddings(self, ids, vectors, metadatas, documents=None):
        for i, id_ in enumerate(ids):
            self._data[id_] = {
                "vector": vectors[i],
                "metadata": metadatas[i],
                "document": documents[i] if documents else None,
            }

    def search(self, query_vector, top_k=5, filter_conditions=None):
        results = []
        for id_, item in self._data.items():
            if filter_conditions:
                match = all(
                    item["metadata"].get(k) == v
                    for k, v in filter_conditions.items()
                )
                if not match:
                    continue
            results.append(SearchResult(
                id=id_,
                score=0.9,
                content=item.get("document"),
                metadata=item["metadata"],
            ))
        return sorted(results, key=lambda r: r.score, reverse=True)[:top_k]

    def delete(self, ids):
        for id_ in ids:
            self._data.pop(id_, None)

    def delete_by_metadata(self, filter_conditions):
        to_delete = [
            id_ for id_, item in self._data.items()
            if all(item["metadata"].get(k) == v for k, v in filter_conditions.items())
        ]
        for id_ in to_delete:
            self._data.pop(id_, None)
        return len(to_delete)

    def count(self, filter_conditions=None):
        if filter_conditions is None:
            return len(self._data)
        return sum(
            1 for item in self._data.values()
            if all(item["metadata"].get(k) == v for k, v in filter_conditions.items())
        )


class MockLLMBackend(LLMBackend):
    """LLMBackend 的 Mock 实现"""

    async def generate(self, messages, temperature=0.7, max_tokens=2048) -> str:
        return "Mock response"

    async def generate_stream(self, messages, temperature=0.7, max_tokens=2048) -> AsyncIterator[str]:
        for token in ["Mock ", "response"]:
            yield token

    @property
    def model_name(self) -> str:
        return "mock-model"


class MockRetriever(Retriever):
    """Retriever 的 Mock 实现"""

    def retrieve(self, query, top_k=5, filter_conditions=None):
        return [
            SearchResult(
                id="chunk_1",
                score=0.95,
                metadata={"content_preview": query[:100], "document_id": "doc_1"},
            )
        ]


# =========================================================================
# 测试：抽象类不能直接实例化
# =========================================================================

class TestAbstractClassesCannotBeInstantiated:
    """验证所有抽象类不能直接实例化"""

    def test_document_parser_abstract(self):
        with pytest.raises(TypeError):
            DocumentParser()

    def test_text_splitter_abstract(self):
        with pytest.raises(TypeError):
            TextSplitter()

    def test_embedding_backend_abstract(self):
        with pytest.raises(TypeError):
            EmbeddingBackend()

    def test_vector_store_abstract(self):
        with pytest.raises(TypeError):
            VectorStore()

    def test_llm_backend_abstract(self):
        with pytest.raises(TypeError):
            LLMBackend()

    def test_retriever_abstract(self):
        with pytest.raises(TypeError):
            Retriever()


# =========================================================================
# 测试：Mock 实现可以正确调用所有方法
# =========================================================================

class TestMockDocumentParser:
    """验证 DocumentParser Mock 实现"""

    def test_parse_returns_parsed_document(self):
        parser = MockDocumentParser()
        result = parser.parse("/path/to/test.txt")
        assert isinstance(result, ParsedDocument)
        assert result.content == "test"
        assert result.metadata["source"] == "/path/to/test.txt"
        assert result.sections == []

    def test_supported_extensions(self):
        exts = MockDocumentParser.supported_extensions()
        assert ".txt" in exts
        assert ".md" in exts


class TestMockTextSplitter:
    """验证 TextSplitter Mock 实现"""

    def test_split_returns_chunks(self):
        splitter = MockTextSplitter()
        chunks = splitter.split("hello world")
        assert len(chunks) == 1
        assert isinstance(chunks[0], DocumentChunk)
        assert chunks[0].content == "hello world"
        assert chunks[0].chunk_index == 0

    def test_split_with_metadata(self):
        splitter = MockTextSplitter()
        chunks = splitter.split("text", metadata={"doc_id": "123"})
        assert chunks[0].metadata["doc_id"] == "123"

    def test_type_name(self):
        splitter = MockTextSplitter()
        assert splitter.type_name == "mock"


class TestMockEmbeddingBackend:
    """验证 EmbeddingBackend Mock 实现"""

    def test_embed_text(self):
        emb = MockEmbeddingBackend()
        vec = emb.embed_text("hello")
        assert isinstance(vec, list)
        assert all(isinstance(v, float) for v in vec)

    def test_embed_documents(self):
        emb = MockEmbeddingBackend()
        vecs = emb.embed_documents(["a", "b", "c"])
        assert len(vecs) == 3
        assert all(len(v) == 3 for v in vecs)

    def test_dimension(self):
        emb = MockEmbeddingBackend()
        assert emb.dimension == 3


class TestMockVectorStore:
    """验证 VectorStore Mock 实现"""

    @pytest.fixture
    def store(self):
        vs = MockVectorStore()
        vs.add_embeddings(
            ids=["1", "2", "3"],
            vectors=[[0.1] * 3, [0.2] * 3, [0.3] * 3],
            metadatas=[
                {"dataset_id": "ds1", "user_id": "u1"},
                {"dataset_id": "ds1", "user_id": "u1"},
                {"dataset_id": "ds2", "user_id": "u2"},
            ],
        )
        return vs

    def test_add_embeddings_and_count(self, store):
        assert store.count() == 3

    def test_search(self, store):
        results = store.search(query_vector=[0.1] * 3, top_k=2)
        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.score == 0.9 for r in results)

    def test_search_with_filter(self, store):
        results = store.search(
            query_vector=[0.1] * 3,
            top_k=5,
            filter_conditions={"dataset_id": "ds1"},
        )
        assert len(results) == 2

    def test_delete(self, store):
        store.delete(["1"])
        assert store.count() == 2

    def test_delete_by_metadata(self, store):
        deleted = store.delete_by_metadata({"dataset_id": "ds1"})
        assert deleted == 2
        assert store.count() == 1

    def test_count_with_filter(self, store):
        assert store.count(filter_conditions={"dataset_id": "ds1"}) == 2
        assert store.count(filter_conditions={"dataset_id": "ds2"}) == 1

    def test_count_no_filter(self, store):
        assert store.count() == 3


class TestMockLLMBackend:
    """验证 LLMBackend Mock 实现"""

    @pytest.mark.asyncio
    async def test_generate(self):
        llm = MockLLMBackend()
        result = await llm.generate([{"role": "user", "content": "hi"}])
        assert isinstance(result, str)
        assert result == "Mock response"

    @pytest.mark.asyncio
    async def test_generate_stream(self):
        llm = MockLLMBackend()
        tokens = []
        async for token in llm.generate_stream([{"role": "user", "content": "hi"}]):
            tokens.append(token)
        assert len(tokens) > 0
        assert "".join(tokens) == "Mock response"

    def test_model_name(self):
        llm = MockLLMBackend()
        assert llm.model_name == "mock-model"


class TestMockRetriever:
    """验证 Retriever Mock 实现"""

    def test_retrieve(self):
        retriever = MockRetriever()
        results = retriever.retrieve("test query", top_k=3)
        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        assert results[0].id == "chunk_1"
        assert results[0].score == 0.95

    def test_retrieve_with_filter(self):
        retriever = MockRetriever()
        results = retriever.retrieve("query", top_k=5, filter_conditions={"dataset_id": "ds1"})
        assert len(results) == 1

    def test_retrieve_default_top_k(self):
        """验证 top_k 默认值为 5"""
        import inspect
        sig = inspect.signature(Retriever.retrieve)
        assert sig.parameters["top_k"].default == 5


# =========================================================================
# 测试：dataclass 默认值和字段
# =========================================================================

class TestParsedDocumentDataclass:
    """验证 ParsedDocument dataclass"""

    def test_default_metadata(self):
        doc = ParsedDocument(content="hello")
        assert doc.metadata == {}
        assert doc.sections == []

    def test_fields(self):
        field_names = {f.name for f in fields(ParsedDocument)}
        assert field_names == {"content", "metadata", "sections"}

    def test_content_required(self):
        with pytest.raises(TypeError):
            ParsedDocument()


class TestDocumentChunkDataclass:
    """验证 DocumentChunk dataclass"""

    def test_default_metadata(self):
        chunk = DocumentChunk(content="hello", chunk_index=0)
        assert chunk.metadata == {}

    def test_fields(self):
        field_names = {f.name for f in fields(DocumentChunk)}
        assert field_names == {"content", "chunk_index", "metadata"}

    def test_content_and_index_required(self):
        with pytest.raises(TypeError):
            DocumentChunk()
        with pytest.raises(TypeError):
            DocumentChunk(content="hello")


class TestSearchResultDataclass:
    """验证 SearchResult dataclass"""

    def test_default_content(self):
        sr = SearchResult(id="1", score=0.9, metadata={"k": "v"})
        assert sr.content is None

    def test_fields(self):
        field_names = {f.name for f in fields(SearchResult)}
        assert field_names == {"id", "score", "metadata", "content"}

    def test_required_fields(self):
        with pytest.raises(TypeError):
            SearchResult()
        with pytest.raises(TypeError):
            SearchResult(id="1")
        with pytest.raises(TypeError):
            SearchResult(id="1", score=0.9)


# =========================================================================
# 测试：接口方法签名
# =========================================================================

class TestInterfaceSignatures:
    """验证接口方法参数签名正确"""

    def test_document_parser_parse_signature(self):
        import inspect
        sig = inspect.signature(DocumentParser.parse)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "file_path" in params

    def test_text_splitter_split_signature(self):
        import inspect
        sig = inspect.signature(TextSplitter.split)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "text" in params
        assert "metadata" in params

    def test_embedding_embed_text_signature(self):
        import inspect
        sig = inspect.signature(EmbeddingBackend.embed_text)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "text" in params

    def test_vector_store_search_signature(self):
        import inspect
        sig = inspect.signature(VectorStore.search)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "query_vector" in params
        assert "top_k" in params
        assert "filter_conditions" in params

    def test_llm_generate_signature(self):
        import inspect
        sig = inspect.signature(LLMBackend.generate)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "messages" in params
        assert "temperature" in params
        assert "max_tokens" in params

    def test_retriever_retrieve_signature(self):
        import inspect
        sig = inspect.signature(Retriever.retrieve)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "query" in params
        assert "top_k" in params
        assert "filter_conditions" in params

    def test_all_interfaces_exported(self):
        """验证 interfaces 包导出了所有预期的类和 dataclass"""
        expected = {
            "DocumentParser", "ParsedDocument",
            "TextSplitter", "DocumentChunk",
            "EmbeddingBackend",
            "VectorStore", "SearchResult",
            "LLMBackend",
            "Retriever",
        }
        from app.rag.interfaces import __all__ as exported
        assert set(exported) == expected
