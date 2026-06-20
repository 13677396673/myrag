"""
VectorRetriever 单元测试

测试策略：
- 使用 MagicMock 模拟 EmbeddingBackend（返回固定向量）
- 使用 MagicMock 模拟 VectorStore（返回固定结果）
- 验证 retrieve 正确调用了 embed_text → search
- 验证 filter_conditions 透传
- 验证 top_k 参数传递
- 验证 similarity_threshold 过滤
"""

from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from app.rag.retrievers import VectorRetriever
from app.rag.interfaces.vector_store import SearchResult


class TestVectorRetriever:
    """VectorRetriever 单元测试"""

    # ── 初始化 ──

    def test_init(self):
        """测试基本初始化"""
        emb = MagicMock()
        store = MagicMock()
        retriever = VectorRetriever(embedding=emb, vector_store=store)

        assert retriever.embedding is emb
        assert retriever.vector_store is store

    def test_init_with_custom_defaults(self):
        """测试带自定义默认参数的初始化"""
        emb = MagicMock()
        store = MagicMock()
        retriever = VectorRetriever(
            embedding=emb,
            vector_store=store,
            top_k=10,
            similarity_threshold=0.5,
        )

        assert retriever._default_top_k == 10
        assert retriever._similarity_threshold == 0.5

    def test_init_default_threshold(self):
        """测试默认 similarity_threshold 为 0.0（不过滤）"""
        emb = MagicMock()
        store = MagicMock()
        retriever = VectorRetriever(embedding=emb, vector_store=store)

        assert retriever._similarity_threshold == 0.0

    # ── 基本检索流程 ──

    def test_retrieve_calls_embed_text_and_search(self):
        """测试 retrieve 正确调用了 embed_text → search"""
        emb = MagicMock()
        emb.embed_text.return_value = [0.1, 0.2, 0.3]

        store = MagicMock()
        store.search.return_value = [
            SearchResult(id="1", score=0.9, metadata={"title": "doc1"}),
            SearchResult(id="2", score=0.8, metadata={"title": "doc2"}),
        ]

        retriever = VectorRetriever(embedding=emb, vector_store=store)
        results = retriever.retrieve("测试查询", top_k=5)

        # 验证 embed_text 被调用
        emb.embed_text.assert_called_once_with("测试查询")

        # 验证 search 被调用，且传递了正确的参数
        store.search.assert_called_once_with(
            query_vector=[0.1, 0.2, 0.3],
            top_k=5,
            filter_conditions=None,
        )

        # 验证返回结果
        assert len(results) == 2
        assert results[0].id == "1"
        assert results[0].score == 0.9
        assert results[1].id == "2"
        assert results[1].score == 0.8

    def test_retrieve_uses_default_top_k(self):
        """测试 retrieve 使用默认 top_k 当不传参时"""
        emb = MagicMock()
        emb.embed_text.return_value = [0.1, 0.2, 0.3]

        store = MagicMock()
        store.search.return_value = [
            SearchResult(id="1", score=0.9, metadata={}),
        ]

        retriever = VectorRetriever(embedding=emb, vector_store=store, top_k=10)
        retriever.retrieve("查询")

        store.search.assert_called_once_with(
            query_vector=[0.1, 0.2, 0.3],
            top_k=5,  # retrieve() 显式传参优先于默认值
            filter_conditions=None,
        )

    def test_retrieve_with_custom_top_k(self):
        """测试 retrieve 自定义 top_k"""
        emb = MagicMock()
        emb.embed_text.return_value = [0.1, 0.2, 0.3]
        store = MagicMock()
        store.search.return_value = []

        retriever = VectorRetriever(embedding=emb, vector_store=store)
        retriever.retrieve("查询", top_k=20)

        store.search.assert_called_once_with(
            query_vector=[0.1, 0.2, 0.3],
            top_k=20,
            filter_conditions=None,
        )

    # ── filter_conditions 透传 ──

    def test_retrieve_passes_filter_conditions(self):
        """测试 filter_conditions 被正确透传给 vector_store.search"""
        emb = MagicMock()
        emb.embed_text.return_value = [0.1, 0.2, 0.3]
        store = MagicMock()
        store.search.return_value = []

        retriever = VectorRetriever(embedding=emb, vector_store=store)
        retriever.retrieve(
            "查询",
            top_k=5,
            filter_conditions={"dataset_id": "ds-001", "user_id": "user-1"},
        )

        store.search.assert_called_once_with(
            query_vector=[0.1, 0.2, 0.3],
            top_k=5,
            filter_conditions={"dataset_id": "ds-001", "user_id": "user-1"},
        )

    def test_retrieve_passes_empty_filter_conditions(self):
        """测试传递空 dict 作为 filter_conditions"""
        emb = MagicMock()
        emb.embed_text.return_value = [0.1, 0.2, 0.3]
        store = MagicMock()
        store.search.return_value = []

        retriever = VectorRetriever(embedding=emb, vector_store=store)
        retriever.retrieve("查询", top_k=5, filter_conditions={})

        store.search.assert_called_once_with(
            query_vector=[0.1, 0.2, 0.3],
            top_k=5,
            filter_conditions={},
        )

    # ── 相似度阈值过滤 ──

    def test_retrieve_filters_by_similarity_threshold(self):
        """测试 similarity_threshold 过滤低分结果"""
        emb = MagicMock()
        emb.embed_text.return_value = [0.1, 0.2, 0.3]

        store = MagicMock()
        store.search.return_value = [
            SearchResult(id="1", score=0.9, metadata={}),
            SearchResult(id="2", score=0.6, metadata={}),
            SearchResult(id="3", score=0.4, metadata={}),
            SearchResult(id="4", score=0.3, metadata={}),
        ]

        retriever = VectorRetriever(
            embedding=emb,
            vector_store=store,
            similarity_threshold=0.5,
        )
        results = retriever.retrieve("查询")

        # 只有 score >= 0.5 的结果被保留
        assert len(results) == 2
        assert results[0].id == "1"
        assert results[1].id == "2"

    def test_retrieve_threshold_zero_keeps_all(self):
        """测试 similarity_threshold=0.0 不过滤任何结果"""
        emb = MagicMock()
        emb.embed_text.return_value = [0.1, 0.2, 0.3]

        store = MagicMock()
        store.search.return_value = [
            SearchResult(id="1", score=0.1, metadata={}),
            SearchResult(id="2", score=0.01, metadata={}),
            SearchResult(id="3", score=0.001, metadata={}),
        ]

        retriever = VectorRetriever(embedding=emb, vector_store=store, similarity_threshold=0.0)
        results = retriever.retrieve("查询")

        assert len(results) == 3

    def test_retrieve_threshold_all_below_returns_empty(self):
        """测试所有结果都低于阈值时返回空列表"""
        emb = MagicMock()
        emb.embed_text.return_value = [0.1, 0.2, 0.3]

        store = MagicMock()
        store.search.return_value = [
            SearchResult(id="1", score=0.3, metadata={}),
            SearchResult(id="2", score=0.2, metadata={}),
        ]

        retriever = VectorRetriever(
            embedding=emb,
            vector_store=store,
            similarity_threshold=0.5,
        )
        results = retriever.retrieve("查询")

        assert len(results) == 0

    # ── 空结果处理 ──

    def test_retrieve_empty_results(self):
        """测试 VectorStore 返回空列表时检索器也返回空列表"""
        emb = MagicMock()
        emb.embed_text.return_value = [0.1, 0.2, 0.3]
        store = MagicMock()
        store.search.return_value = []

        retriever = VectorRetriever(embedding=emb, vector_store=store)
        results = retriever.retrieve("查询")

        assert isinstance(results, list)
        assert len(results) == 0

    # ── 属性 ──

    def test_embedding_property(self):
        """测试 embedding 属性返回正确的实例"""
        emb = MagicMock()
        store = MagicMock()
        retriever = VectorRetriever(embedding=emb, vector_store=store)

        assert retriever.embedding is emb

    def test_vector_store_property(self):
        """测试 vector_store 属性返回正确的实例"""
        emb = MagicMock()
        store = MagicMock()
        retriever = VectorRetriever(embedding=emb, vector_store=store)

        assert retriever.vector_store is store


class TestVectorRetrieverFactory:
    """create_retriever 工厂函数测试"""

    @staticmethod
    def _make_settings(mode: str = "vector", top_k: int = 5, threshold: float = 0.0):
        """创建一个模拟的 settings 对象"""
        settings = MagicMock()
        settings.RETRIEVAL_MODE = mode
        settings.RETRIEVAL_TOP_K = top_k
        settings.RETRIEVAL_SIMILARITY_THRESHOLD = threshold
        return settings

    def test_create_vector_retriever(self):
        """测试创建 VectorRetriever"""
        from app.rag.retrievers import create_retriever

        settings = self._make_settings(mode="vector")
        emb = MagicMock()
        store = MagicMock()

        retriever = create_retriever(settings, embedding=emb, vector_store=store)

        assert isinstance(retriever, VectorRetriever)
        assert retriever.embedding is emb
        assert retriever.vector_store is store
        assert retriever._default_top_k == 5
        assert retriever._similarity_threshold == 0.0

    def test_create_vector_retriever_custom_defaults(self):
        """测试创建 VectorRetriever 使用自定义默认值"""
        from app.rag.retrievers import create_retriever

        settings = self._make_settings(mode="vector", top_k=10, threshold=0.7)
        emb = MagicMock()
        store = MagicMock()

        retriever = create_retriever(settings, embedding=emb, vector_store=store)

        assert retriever._default_top_k == 10
        assert retriever._similarity_threshold == 0.7

    def test_create_hybrid_retriever(self):
        """测试创建 HybridRetriever"""
        from app.rag.retrievers import create_retriever, HybridRetriever, VectorRetriever

        settings = self._make_settings(mode="hybrid")
        emb = MagicMock()
        store = MagicMock()

        retriever = create_retriever(settings, embedding=emb, vector_store=store)

        assert isinstance(retriever, HybridRetriever)
        assert isinstance(retriever.vector_retriever, VectorRetriever)
        assert retriever.vector_retriever.embedding is emb
        assert retriever.vector_retriever.vector_store is store

    def test_unsupported_mode_raises(self):
        """测试不支持的 RETRIEVAL_MODE 抛出 ValueError"""
        from app.rag.retrievers import create_retriever

        settings = self._make_settings(mode="invalid")

        with pytest.raises(ValueError, match="不支持的 RETRIEVAL_MODE"):
            create_retriever(settings, embedding=MagicMock(), vector_store=MagicMock())
