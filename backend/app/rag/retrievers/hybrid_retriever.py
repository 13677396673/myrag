"""混合检索器 — 向量检索 + BM25 关键词检索（RRF 融合）

``HybridRetriever`` 将语义检索（``VectorRetriever``）和关键词检索（``BM25Retriever``）
的结果通过 Reciprocal Rank Fusion (RRF) 算法进行融合排序。

RRF 公式::

    score(d) = Σ 1 / (k + rank_s(d))

其中 ``rank_s(d)`` 是文档 d 在检索方式 s 中的排名，``k`` 为平滑常数（默认 60）。
RRF 不需要分数归一化，不同检索方式的分数可直接融合。

用法::

    from app.rag.retrievers import VectorRetriever, BM25Retriever, HybridRetriever

    hybrid = HybridRetriever(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
        top_k=5,
    )
    results = hybrid.retrieve("什么是 RAG？")
"""

from typing import List, Optional, Dict

from app.rag.interfaces.retriever import Retriever
from app.rag.interfaces.vector_store import SearchResult


class HybridRetriever(Retriever):
    """混合检索器（向量 + BM25，RRF 融合）

    内部持有 ``VectorRetriever`` 和 ``BM25Retriever`` 各一个实例，
    每次 ``retrieve()`` 时：

    1. 从两路各检索 ``top_k * 3`` 个候选结果
    2. 使用 RRF 算法计算每个文档的融合得分
    3. 取融合得分最高的 ``top_k`` 个结果返回

    参数:
        vector_retriever: 语义检索器实例
        bm25_retriever: BM25 关键词检索器实例
        top_k: 默认检索数量（可在 ``retrieve`` 调用时覆盖）
        rrf_k: RRF 平滑常数 k（默认 60），越大则排名差异的影响越小
    """

    def __init__(
        self,
        vector_retriever: Retriever,
        bm25_retriever: Retriever,
        top_k: int = 5,
        rrf_k: int = 60,
    ):
        self._vector_retriever = vector_retriever
        self._bm25_retriever = bm25_retriever
        self._default_top_k = top_k
        self._rrf_k = rrf_k

    # ── 公开方法 ──────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_conditions: Optional[dict] = None,
    ) -> List[SearchResult]:
        """执行混合检索

        执行流程：
        1. 从 ``VectorRetriever`` 检索 ``top_k * 3`` 个结果
        2. 从 ``BM25Retriever`` 检索 ``top_k * 3`` 个结果
        3. 用 RRF 计算融合排名分
        4. 按融合分降序排列，取 ``top_k``

        参数:
            query: 用户查询文本
            top_k: 返回的最相关结果数量
            filter_conditions: 可选的元数据过滤条件（透传给两路检索器）

        返回:
            按 RRF 融合得分降序排列的 SearchResult 列表
        """
        # 多取一些候选供 RRF 排序
        candidate_k = top_k * 3

        # 1. 两路检索
        vector_results = self._vector_retriever.retrieve(
            query=query,
            top_k=candidate_k,
            filter_conditions=filter_conditions,
        )
        bm25_results = self._bm25_retriever.retrieve(
            query=query,
            top_k=candidate_k,
            filter_conditions=filter_conditions,
        )

        # 2. RRF 融合
        return self._rrf_fusion(vector_results, bm25_results, top_k)

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _rrf_fusion(
        self,
        vector_results: List[SearchResult],
        bm25_results: List[SearchResult],
        top_k: int,
    ) -> List[SearchResult]:
        """Reciprocal Rank Fusion 融合排序

        对两路检索结果中出现的每个文档，累加其在各路中的 RRF 得分：
        ``1 / (k + rank)``。其中 ``rank`` 从 1 开始计数。

        参数:
            vector_results: 向量检索结果（按得分降序）
            bm25_results: BM25 检索结果（按得分降序）
            top_k: 返回结果数量

        返回:
            按 RRF 得分降序排列的 SearchResult 列表
        """
        # 累加 RRF 得分
        rrf_scores: Dict[str, float] = {}

        for rank, result in enumerate(vector_results):
            rrf_scores[result.id] = rrf_scores.get(result.id, 0.0) + 1.0 / (self._rrf_k + rank + 1)

        for rank, result in enumerate(bm25_results):
            rrf_scores[result.id] = rrf_scores.get(result.id, 0.0) + 1.0 / (self._rrf_k + rank + 1)

        # 按 RRF 得分降序排列
        ranked_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # 建立 id → SearchResult 映射（优先取 vector 的结果，保 metadata 和 content 完整）
        id_to_result: Dict[str, SearchResult] = {}
        for r in vector_results + bm25_results:
            if r.id not in id_to_result:
                id_to_result[r.id] = r

        # 组装最终结果
        results: List[SearchResult] = []
        for doc_id, rrf_score in ranked_ids[:top_k]:
            original = id_to_result.get(doc_id)
            if original is None:
                continue
            results.append(SearchResult(
                id=original.id,
                score=rrf_score,
                metadata=original.metadata,
                content=original.content,
            ))

        return results

    # ── 属性 ──────────────────────────────────────────────────────────

    @property
    def vector_retriever(self) -> Retriever:
        """返回内部持有的语义检索器"""
        return self._vector_retriever

    @property
    def bm25_retriever(self) -> Retriever:
        """返回内部持有的 BM25 检索器"""
        return self._bm25_retriever
