"""BM25 关键词检索器（预留占位）

``BM25Retriever`` 基于 BM25 算法实现关键词检索，
不依赖向量化模型，适用于关键词匹配场景。

.. note::

   当前为占位文件，具体实现将在后续迭代中完成。
   计划使用 ``rank_bm25`` 库或自定义实现。
"""

from typing import List, Optional

from app.rag.interfaces.retriever import Retriever
from app.rag.interfaces.vector_store import SearchResult


class BM25Retriever(Retriever):
    """BM25 关键词检索器（预留占位）

    基于 BM25 算法实现关键词级别的文本检索。
    """

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_conditions: Optional[dict] = None,
    ) -> List[SearchResult]:
        """检索方法（暂未实现）

        异常:
            NotImplementedError: BM25 检索尚未实现
        """
        raise NotImplementedError("BM25Retriever 尚未实现")
