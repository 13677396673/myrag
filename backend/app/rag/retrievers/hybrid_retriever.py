"""混合检索器 — 向量检索 + BM25 关键词检索（加权线性融合）

``HybridRetriever`` 将语义检索（``VectorRetriever``）和关键词检索（``BM25Retriever``）
的结果通过加权线性融合（Weighted Linear Fusion）进行融合排序。

融合公式::

    score(d) = vector_weight × vector_sim(d) + keyword_weight × bm25_norm(d)

其中 ``vector_sim`` 由 ChromaDB Cosine 距离转换为 [0,1] 相似度，
``bm25_norm`` 使用 min-max 归一化映射到 [0,1] 区间。

默认权重: vector_weight=0.7, keyword_weight=0.3（与主流实践一致）。

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
    """混合检索器（向量 + BM25，加权线性融合）

    内部持有 ``VectorRetriever`` 和 ``BM25Retriever`` 各一个实例，
    每次 ``retrieve()`` 时：

    1. 从两路各检索 ``top_k * 3`` 个候选结果
    2. 对每篇文档计算加权融合得分
    3. 取融合得分最高的 ``top_k`` 个结果返回

    分数处理：
    - 向量距离 → ``max(0, 1 - distance/2)`` 映射到 [0,1] 相似度
    - BM25 原始分 → min-max 归一化到 [0,1]
    - 最终 = vector_weight × 向量相似度 + keyword_weight × BM25 归一化

    参数:
        vector_retriever: 语义检索器实例
        bm25_retriever: BM25 关键词检索器实例
        top_k: 默认检索数量（可在 ``retrieve`` 调用时覆盖）
        vector_weight: 向量检索权重（默认 0.7）
        keyword_weight: 关键词检索权重（默认 0.3）
    """

    def __init__(
        self,
        vector_retriever: Retriever,
        bm25_retriever: Retriever,
        top_k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        self._vector_retriever = vector_retriever
        self._bm25_retriever = bm25_retriever
        self._default_top_k = top_k
        self._vector_weight = vector_weight
        self._keyword_weight = keyword_weight

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
        3. 将向量距离转为相似度，BM25 分数 min-max 归一化
        4. 加权线性融合，取 ``top_k``

        参数:
            query: 用户查询文本
            top_k: 返回的最相关结果数量
            filter_conditions: 可选的元数据过滤条件（透传给两路检索器）

        返回:
            按加权融合得分降序排列的 SearchResult 列表，分数范围 [0, 1]
        """
        # 多取一些候选供融合排序
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

        # 2. 加权融合
        return self._weighted_fusion(vector_results, bm25_results, top_k)

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _weighted_fusion(
        self,
        vector_results: List[SearchResult],
        bm25_results: List[SearchResult],
        top_k: int,
    ) -> List[SearchResult]:
        """加权线性融合排序

        1. 将 ChromaDB cosine 距离转为 [0,1] 相似度：``sim = max(0, 1 - dist/2)``
        2. BM25 原始分在候选集内做 min-max 归一化
        3. 最终得分 = vector_weight × vector_sim + keyword_weight × bm25_norm

        参数:
            vector_results: 向量检索结果（score 为 cosine distance）
            bm25_results: BM25 检索结果（score 为原始 BM25 分数）
            top_k: 返回结果数量

        返回:
            按加权融合得分降序排列的 SearchResult 列表
        """
        # 处理任意一路为空的情况
        if not vector_results and not bm25_results:
            return []
        if not vector_results:
            return bm25_results[:top_k]
        if not bm25_results:
            return [
                SearchResult(
                    id=r.id,
                    score=max(0.0, 1.0 - r.score / 2.0),
                    metadata=r.metadata,
                    content=r.content,
                )
                for r in vector_results[:top_k]
            ]

        # ── 1. 建立文档池 (doc_id → {vector_sim, bm25_raw, ...}) ──
        pool: Dict[str, dict] = {}
        for r in vector_results:
            pool[r.id] = {
                "vector_sim": max(0.0, 1.0 - r.score / 2.0),
                "bm25_raw": None,
                "metadata": r.metadata,
                "content": r.content,
            }
        for r in bm25_results:
            if r.id in pool:
                pool[r.id]["bm25_raw"] = r.score
            else:
                pool[r.id] = {
                    "vector_sim": 0.0,
                    "bm25_raw": r.score,
                    "metadata": r.metadata,
                    "content": r.content,
                }

        # ── 2. BM25 min-max 归一化 ──
        bm25_vals = [d["bm25_raw"] for d in pool.values() if d["bm25_raw"] is not None]
        if bm25_vals:
            bm25_min, bm25_max = min(bm25_vals), max(bm25_vals)
            bm25_range = bm25_max - bm25_min
        else:
            bm25_min = bm25_max = bm25_range = 0.0

        # ── 3. 计算加权得分 ──
        scored: List[tuple[float, str]] = []
        for doc_id, data in pool.items():
            if bm25_range > 0 and data["bm25_raw"] is not None:
                bm25_norm = (data["bm25_raw"] - bm25_min) / bm25_range
            elif data["bm25_raw"] is not None and data["bm25_raw"] > 0:
                # 所有分数相同且 > 0，视为完全匹配
                bm25_norm = 1.0
            else:
                bm25_norm = 0.0

            final_score = (
                self._vector_weight * data["vector_sim"]
                + self._keyword_weight * bm25_norm
            )
            scored.append((final_score, doc_id))

        # ── 4. 排序取 top_k ──
        scored.sort(key=lambda x: x[0], reverse=True)

        results: List[SearchResult] = []
        for final_score, doc_id in scored[:top_k]:
            data = pool[doc_id]
            results.append(SearchResult(
                id=doc_id,
                score=final_score,
                metadata=data["metadata"],
                content=data["content"],
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
