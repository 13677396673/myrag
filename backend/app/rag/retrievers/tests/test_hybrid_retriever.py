"""
HybridRetriever 单元测试

测试策略：
- 使用 MagicMock 模拟 VectorRetriever 和 BM25Retriever
- 验证 RRF 融合逻辑
- 验证 filter_conditions 透传
- 验证 top_k 参数
"""

from unittest.mock import MagicMock

import pytest

from app.rag.retrievers import HybridRetriever
from app.rag.interfaces.vector_store import SearchResult


class TestHybridRetriever:
    """HybridRetriever 单元测试"""

    # ── 初始化 ──

    def test_init(self):
        """测试基本初始化"""
        vector = MagicMock()
        bm25 = MagicMock()
        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)

        assert hybrid.vector_retriever is vector
        assert hybrid.bm25_retriever is bm25

    def test_init_with_custom_rrf_k(self):
        """测试自定义 RRF k 参数"""
        vector = MagicMock()
        bm25 = MagicMock()
        hybrid = HybridRetriever(
            vector_retriever=vector,
            bm25_retriever=bm25,
            top_k=10,
            rrf_k=30,
        )

        assert hybrid._default_top_k == 10
        assert hybrid._rrf_k == 30

    # ── RRF 融合 ──

    def test_retrieve_calls_both_retrievers(self):
        """测试 retrieve 调用了两路检索器"""
        vector = MagicMock()
        vector.retrieve.return_value = [
            SearchResult(id="1", score=0.9, metadata={}, content="a"),
            SearchResult(id="2", score=0.8, metadata={}, content="b"),
        ]
        bm25 = MagicMock()
        bm25.retrieve.return_value = []

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        hybrid.retrieve("查询", top_k=5)

        vector.retrieve.assert_called_once()
        bm25.retrieve.assert_called_once()

    def test_rrf_fusion_ranks_common_docs_higher(self):
        """测试 RRF 融合：两路都出现的文档得分更高"""
        vector = MagicMock()
        vector.retrieve.return_value = [
            SearchResult(id="A", score=0.9, metadata={}, content="doc A"),
            SearchResult(id="B", score=0.8, metadata={}, content="doc B"),
            SearchResult(id="C", score=0.7, metadata={}, content="doc C"),
        ]
        bm25 = MagicMock()
        bm25.retrieve.return_value = [
            SearchResult(id="B", score=0.9, metadata={}, content="doc B"),
            SearchResult(id="D", score=0.8, metadata={}, content="doc D"),
        ]

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        results = hybrid.retrieve("查询", top_k=4)

        # B 在两路都出现，应该是第1名
        assert results[0].id == "B"
        # 4 个不重复结果
        assert len(results) == 4
        assert {r.id for r in results} == {"A", "B", "C", "D"}

    def test_rrf_fusion_respects_top_k(self):
        """测试 RRF 融合后的 top_k 限制"""
        vector = MagicMock()
        vector.retrieve.return_value = [
            SearchResult(id=str(i), score=1.0 - i * 0.1, metadata={}, content=f"doc{i}")
            for i in range(5)
        ]
        bm25 = MagicMock()
        bm25.retrieve.return_value = [
            SearchResult(id=str(i), score=1.0 - i * 0.1, metadata={}, content=f"doc{i}")
            for i in range(5)
        ]

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        results = hybrid.retrieve("查询", top_k=3)

        assert len(results) == 3

    def test_rrf_fusion_both_empty(self):
        """测试两路都为空时返回空列表"""
        vector = MagicMock()
        vector.retrieve.return_value = []
        bm25 = MagicMock()
        bm25.retrieve.return_value = []

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        results = hybrid.retrieve("查询", top_k=5)

        assert isinstance(results, list)
        assert len(results) == 0

    def test_rrf_fusion_vector_only_results(self):
        """测试仅向量检索有结果"""
        vector = MagicMock()
        vector.retrieve.return_value = [
            SearchResult(id="1", score=0.9, metadata={}, content="a"),
            SearchResult(id="2", score=0.8, metadata={}, content="b"),
        ]
        bm25 = MagicMock()
        bm25.retrieve.return_value = []

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        results = hybrid.retrieve("查询", top_k=5)

        assert len(results) == 2
        assert results[0].id == "1"

    def test_rrf_fusion_bm25_only_results(self):
        """测试仅 BM25 有结果"""
        vector = MagicMock()
        vector.retrieve.return_value = []
        bm25 = MagicMock()
        bm25.retrieve.return_value = [
            SearchResult(id="1", score=0.9, metadata={}, content="a"),
        ]

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        results = hybrid.retrieve("查询", top_k=5)

        assert len(results) == 1
        assert results[0].id == "1"

    # ── filter_conditions 透传 ──

    def test_passes_filter_conditions_to_both(self):
        """测试 filter_conditions 被透传给两路检索器"""
        vector = MagicMock()
        vector.retrieve.return_value = []
        bm25 = MagicMock()
        bm25.retrieve.return_value = []

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        hybrid.retrieve("查询", top_k=5, filter_conditions={"dataset_id": "ds1"})

        vector.retrieve.assert_called_once_with(
            query="查询", top_k=15, filter_conditions={"dataset_id": "ds1"}
        )
        bm25.retrieve.assert_called_once_with(
            query="查询", top_k=15, filter_conditions={"dataset_id": "ds1"}
        )

    # ── RRF 得分正确性 ──

    def test_rrf_score_calculation(self):
        """测试 RRF 分数计算是否正确

        文档 A 在向量检索排第 1，在 BM25 排第 3
        RRF(A) = 1/(60+0) + 1/(60+2) = 1/60 + 1/62 ≈ 0.0328
        """
        vector = MagicMock()
        vector.retrieve.return_value = [
            SearchResult(id="A", score=0.9, metadata={}, content="a"),
            SearchResult(id="B", score=0.8, metadata={}, content="b"),
        ]
        bm25 = MagicMock()
        bm25.retrieve.return_value = [
            SearchResult(id="C", score=0.7, metadata={}, content="c"),
            SearchResult(id="D", score=0.6, metadata={}, content="d"),
            SearchResult(id="A", score=0.5, metadata={}, content="a"),
        ]

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25, rrf_k=60)
        results = hybrid.retrieve("查询", top_k=4)

        # 验证 A 的 RRF 得分 = 1/61 + 1/63
        result_a = next(r for r in results if r.id == "A")
        expected_score = 1.0 / 61 + 1.0 / 63
        assert abs(result_a.score - expected_score) < 0.001

    # ── 属性 ──

    def test_properties(self):
        """测试属性返回正确的实例"""
        vector = MagicMock()
        bm25 = MagicMock()
        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)

        assert hybrid.vector_retriever is vector
        assert hybrid.bm25_retriever is bm25
