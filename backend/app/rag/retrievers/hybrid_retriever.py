"""混合检索器（预留占位）

``HybridRetriever`` 将向量检索与关键词检索（BM25）的结果
进行融合排序，提供更全面的检索能力。

.. note::

   当前为占位文件，具体实现将在后续迭代中完成。
   融合策略计划支持：
   - Reciprocal Rank Fusion (RRF)
   - 加权求和
"""

from typing import List, Optional

from app.rag.interfaces.retriever import Retriever
from app.rag.interfaces.vector_store import SearchResult


class HybridRetriever(Retriever):
    """混合检索器（预留占位）

    将向量检索和 BM25 关键词检索的结果融合排序。
    """

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_conditions: Optional[dict] = None,
    ) -> List[SearchResult]:
        """检索方法（暂未实现）

        异常:
            NotImplementedError: 混合检索尚未实现
        """
        raise NotImplementedError("HybridRetriever 尚未实现")
