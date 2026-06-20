"""BM25 关键词检索器

``BM25Retriever`` 基于 BM25 算法实现关键词检索，
通过 ``VectorStore.get_all()`` 获取全量文档原文，在内存中构建倒排索引。

不依赖向量化模型，适用于关键词精确匹配场景，
与 ``VectorRetriever``（语义检索）互补构成混合检索。

用法::

    from app.rag.retrievers import BM25Retriever
    from app.rag.vector_stores import ChromaDBStore

    store = ChromaDBStore()
    retriever = BM25Retriever(vector_store=store)
    results = retriever.retrieve("什么是 RAG？", top_k=5)
"""

from typing import List, Optional, Dict, Any

import jieba
from rank_bm25 import BM25Okapi

from app.rag.interfaces.retriever import Retriever
from app.rag.interfaces.vector_store import VectorStore, SearchResult


class BM25Retriever(Retriever):
    """BM25 关键词检索器

    使用 ``jieba`` 分词后构建 BM25 倒排索引，
    索引在首次调用 ``retrieve`` 时懒加载构建（从 ``VectorStore.get_all()`` 读取）。

    注意:
        索引是启动后按需构建的内存快照。如果 ``VectorStore`` 中的文档发生变化，
        需调用 ``refresh()`` 重建索引。

    参数:
        vector_store: 实现了 ``VectorStore`` 接口的实例（用于读取全量文档）
        top_k: 默认检索数量（可在 ``retrieve`` 调用时覆盖）
        bm25_k1: BM25 参数 k1，控制词频饱和度（默认 1.5）
        bm25_b: BM25 参数 b，控制文档长度归一化（默认 0.75）
    """

    def __init__(
        self,
        vector_store: VectorStore,
        top_k: int = 5,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
    ):
        self._vector_store = vector_store
        self._default_top_k = top_k
        self._bm25_k1 = bm25_k1
        self._bm25_b = bm25_b

        # 索引状态（懒加载）
        self._corpus: List[Dict[str, Any]] = []   # [{id, content, metadata}]
        self._bm25: Optional[BM25Okapi] = None

    # ── 公开方法 ──────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_conditions: Optional[dict] = None,
    ) -> List[SearchResult]:
        """根据查询文本检索相关文档片段

        执行流程：
        1. 如果索引未构建，调用 ``_build_index()``
        2. 用 ``jieba`` 对查询分词
        3. 调用 ``BM25Okapi.get_scores()`` 计算所有文档得分
        4. 按得分降序排列，取 ``top_k`` 条
        5. 如果传入了 ``filter_conditions``，在排序后过滤（检索更多候选以保证召回）

        参数:
            query: 用户查询文本
            top_k: 返回的最相关结果数量
            filter_conditions: 可选的元数据过滤条件

        返回:
            按 BM25 得分降序排列的 SearchResult 列表
        """
        # 1. 懒加载索引
        if self._bm25 is None:
            self._build_index()

        # 空语料库，直接返回
        if self._bm25 is None:
            return []

        # 2. 查询分词
        query_tokens = self._tokenize(query)

        # 3. BM25 打分
        scores = self._bm25.get_scores(query_tokens)  # List[float]

        # 4. 按得分排序
        indexed = list(enumerate(scores))
        indexed.sort(key=lambda x: x[1], reverse=True)

        # 5. 过滤 + 取 top_k
        #
        # 由于 BM25 索引是全局的，无法在检索时按 metadata 预过滤。
        # 策略：如果传了 filter_conditions，多取一些候选再进行后过滤。
        need = top_k * 3 if filter_conditions else top_k
        candidates: List[SearchResult] = []
        for idx, score in indexed:
            if len(candidates) >= need:
                break
            doc = self._corpus[idx]
            if filter_conditions and not self._match_filters(doc["metadata"], filter_conditions):
                continue
            candidates.append(SearchResult(
                id=doc["id"],
                score=float(score),
                metadata=doc["metadata"],
                content=doc["content"],
            ))

        return candidates[:top_k]

    def refresh(self) -> None:
        """强制重建 BM25 索引

        当 ``VectorStore`` 中的文档发生增删后调用此方法，
        使检索器反映最新的语料状态。
        """
        self._corpus.clear()
        self._bm25 = None
        self._build_index()

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _build_index(self) -> None:
        """从 VectorStore 加载所有文档，构建 BM25 索引

        如果语料库为空，不会创建 BM25 实例，
        后续 ``retrieve()`` 将直接返回空列表。
        """
        docs = self._vector_store.get_all()

        if not docs:
            self._corpus = []
            self._bm25 = None
            return

        tokenized_corpus: List[List[str]] = []
        self._corpus = []  # 重置

        for doc in docs:
            tokens = self._tokenize(doc.content)
            self._corpus.append({
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata,
            })
            tokenized_corpus.append(tokens)

        self._bm25 = BM25Okapi(
            tokenized_corpus,
            k1=self._bm25_k1,
            b=self._bm25_b,
        )

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """对文本进行分词（中英文混合）

        使用 ``jieba.lcut`` 处理中文文本，英文单词会被 jieba 自动识别为独立 token。
        空字符串返回空列表。

        参数:
            text: 原始文本

        返回:
            分词后的 token 列表
        """
        if not text:
            return []
        return list(jieba.lcut(text))

    @staticmethod
    def _match_filters(
        metadata: Dict[str, Any],
        filter_conditions: Dict[str, Any],
    ) -> bool:
        """检查 metadata 是否满足 filter_conditions（简单等值匹配）

        支持由 ``$and``、``$or`` 等操作符组成的嵌套条件，格式与 ChromaDB 的 ``where`` 一致。
        当前实现仅支持顶层等值条件，如 ``{"dataset_id": "xxx"}``。

        参数:
            metadata: 文档的元数据字典
            filter_conditions: 过滤条件

        返回:
            True 表示满足条件
        """
        for key, value in filter_conditions.items():
            if key in ("$and", "$or"):
                # ChromaDB 支持 $and / $or 操作符，当前简化处理
                if key == "$and":
                    if not all(
                        cls._match_filters(metadata, cond)
                        for cond in value
                    ):
                        return False
                elif key == "$or":
                    if not any(
                        cls._match_filters(metadata, cond)
                        for cond in value
                    ):
                        return False
            elif isinstance(value, dict):
                # ChromaDB 条件操作符: $gt, $gte, $lt, $lte, $ne, $in, $nin
                op, operand = next(iter(value.items()))
                meta_val = metadata.get(key)
                if op == "$eq":
                    if meta_val != operand:
                        return False
                elif op == "$ne":
                    if meta_val == operand:
                        return False
                elif op == "$gt":
                    if not (meta_val is not None and meta_val > operand):
                        return False
                elif op == "$gte":
                    if not (meta_val is not None and meta_val >= operand):
                        return False
                elif op == "$lt":
                    if not (meta_val is not None and meta_val < operand):
                        return False
                elif op == "$lte":
                    if not (meta_val is not None and meta_val <= operand):
                        return False
                elif op == "$in":
                    if meta_val not in operand:
                        return False
                elif op == "$nin":
                    if meta_val in operand:
                        return False
            elif metadata.get(key) != value:
                return False
        return True

    # ── 属性 ──────────────────────────────────────────────────────────

    @property
    def is_index_built(self) -> bool:
        """索引是否已构建"""
        return self._bm25 is not None

    @property
    def corpus_size(self) -> int:
        """语料库文档数量"""
        return len(self._corpus)

    @property
    def vector_store(self) -> VectorStore:
        """返回当前使用的 VectorStore 实例"""
        return self._vector_store
