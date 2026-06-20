"""
HybridRetriever 单元测试

测试策略：
- 使用 MagicMock 模拟 VectorRetriever 和 BM25Retriever
- 验证加权线性融合逻辑
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

    def test_init_with_custom_weights(self):
        """测试自定义权重参数"""
        vector = MagicMock()
        bm25 = MagicMock()
        hybrid = HybridRetriever(
            vector_retriever=vector,
            bm25_retriever=bm25,
            top_k=10,
            vector_weight=0.6,
            keyword_weight=0.4,
        )

        assert hybrid._default_top_k == 10
        assert hybrid._vector_weight == 0.6
        assert hybrid._keyword_weight == 0.4

    # ── 加权融合 ──

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

    def test_weighted_fusion_ranks_common_docs_higher(self):
        """测试加权融合：两路都出现的文档因双路得分叠加而排名更高

        文档 B 在两路都出现，得分 = 0.7 × sim(B) + 0.3 × bm25_norm(B)
        文档 A 仅在向量路，得分 = 0.7 × sim(A) + 0.3 × 0
        → B 的最终得分应高于 A
        """
        vector = MagicMock()
        vector.retrieve.return_value = [
            SearchResult(id="A", score=0.3, metadata={}, content="doc A"),
            SearchResult(id="B", score=0.4, metadata={}, content="doc B"),
            SearchResult(id="C", score=0.5, metadata={}, content="doc C"),
        ]
        bm25 = MagicMock()
        bm25.retrieve.return_value = [
            SearchResult(id="B", score=100.0, metadata={}, content="doc B"),
            SearchResult(id="D", score=80.0, metadata={}, content="doc D"),
        ]

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        results = hybrid.retrieve("查询", top_k=4)

        # B 在两路都出现，应该是第1名
        assert results[0].id == "B"
        # 4 个不重复结果
        assert len(results) == 4
        assert {r.id for r in results} == {"A", "B", "C", "D"}

    def test_weighted_fusion_respects_top_k(self):
        """测试加权融合后的 top_k 限制"""
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

    def test_weighted_fusion_both_empty(self):
        """测试两路都为空时返回空列表"""
        vector = MagicMock()
        vector.retrieve.return_value = []
        bm25 = MagicMock()
        bm25.retrieve.return_value = []

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        results = hybrid.retrieve("查询", top_k=5)

        assert isinstance(results, list)
        assert len(results) == 0

    def test_weighted_fusion_vector_only_results(self):
        """测试仅向量检索有结果：分数应被转换为相似度"""
        vector = MagicMock()
        vector.retrieve.return_value = [
            SearchResult(id="1", score=0.2, metadata={}, content="a"),
            SearchResult(id="2", score=0.6, metadata={}, content="b"),
        ]
        bm25 = MagicMock()
        bm25.retrieve.return_value = []

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        results = hybrid.retrieve("查询", top_k=5)

        assert len(results) == 2
        assert results[0].id == "1"
        # 距离 0.2 → 相似度 0.9，距离 0.6 → 相似度 0.7
        assert abs(results[0].score - 0.9) < 0.001

    def test_weighted_fusion_bm25_only_results(self):
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

    # ── 加权得分正确性 ──

    def test_weighted_score_calculation(self):
        """测试加权分数计算是否正确

        文档 A: vector 距离 0.2 → sim=0.9, BM25=100
        文档 B: vector 距离 0.6 → sim=0.7, BM25=60
        文档 C: vector 距离 0.4 → sim=0.8, BM25=80

        BM25 min=60, max=100, range=40
        BM25 norm: A=1.0, B=0.0, C=0.5

        最终分 (0.7/0.3):
        A = 0.7×0.9 + 0.3×1.0 = 0.93
        C = 0.7×0.8 + 0.3×0.5 = 0.71
        B = 0.7×0.7 + 0.3×0.0 = 0.49
        """
        vector = MagicMock()
        vector.retrieve.return_value = [
            SearchResult(id="A", score=0.2, metadata={}, content="a"),
            SearchResult(id="B", score=0.6, metadata={}, content="b"),
            SearchResult(id="C", score=0.4, metadata={}, content="c"),
        ]
        bm25 = MagicMock()
        bm25.retrieve.return_value = [
            SearchResult(id="A", score=100.0, metadata={}, content="a"),
            SearchResult(id="C", score=80.0, metadata={}, content="c"),
            SearchResult(id="B", score=60.0, metadata={}, content="b"),
        ]

        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)
        results = hybrid.retrieve("查询", top_k=3)

        assert len(results) == 3
        assert results[0].id == "A"
        assert results[1].id == "C"
        assert results[2].id == "B"
        assert abs(results[0].score - 0.93) < 0.001
        assert abs(results[1].score - 0.71) < 0.001
        assert abs(results[2].score - 0.49) < 0.001

    # ── 属性 ──

    def test_properties(self):
        """测试属性返回正确的实例"""
        vector = MagicMock()
        bm25 = MagicMock()
        hybrid = HybridRetriever(vector_retriever=vector, bm25_retriever=bm25)

        assert hybrid.vector_retriever is vector
        assert hybrid.bm25_retriever is bm25
