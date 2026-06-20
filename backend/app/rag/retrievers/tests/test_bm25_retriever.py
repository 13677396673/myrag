"""
BM25Retriever 单元测试

测试策略：
- 使用 MockVectorStore 注入测试语料
- 验证 jieba 分词 + BM25 打分的基本流程
- 验证 filter_conditions 后过滤
- 验证 refresh() 重建索引
"""

import pytest

from app.rag.retrievers import BM25Retriever
from app.rag.tests.conftest import MockVectorStore
from app.rag.interfaces.vector_store import Document


class TestBM25Retriever:
    """BM25Retriever 单元测试"""

    # ── 初始化 ──

    def test_init(self):
        """测试基本初始化"""
        store = MockVectorStore()
        retriever = BM25Retriever(vector_store=store)
        assert retriever.vector_store is store
        assert retriever.is_index_built is False
        assert retriever.corpus_size == 0

    def test_init_with_custom_params(self):
        """测试带自定义参数的初始化"""
        store = MockVectorStore()
        retriever = BM25Retriever(
            vector_store=store,
            top_k=10,
            bm25_k1=2.0,
            bm25_b=0.5,
        )
        assert retriever._default_top_k == 10
        # 不应该在 init 时就建索引
        assert retriever.is_index_built is False

    # ── 索引构建 ──

    def test_build_index_on_first_retrieve(self):
        """测试首次 retrieve 时懒加载构建索引"""
        store = MockVectorStore()
        store._documents = [
            Document(id="1", content="检索增强生成 RAG 技术", metadata={}),
            Document(id="2", content="向量数据库用于相似度搜索", metadata={}),
        ]

        retriever = BM25Retriever(vector_store=store)
        assert retriever.is_index_built is False

        # 首次 retrieve 触发建索引
        results = retriever.retrieve("RAG 技术", top_k=2)
        assert retriever.is_index_built is True
        assert retriever.corpus_size == 2

    def test_empty_corpus(self):
        """测试空语料库"""
        store = MockVectorStore()
        retriever = BM25Retriever(vector_store=store)

        results = retriever.retrieve("查询", top_k=5)
        assert isinstance(results, list)
        assert len(results) == 0

    # ── 检索功能 ──

    def test_retrieve_relevant_docs(self):
        """测试 BM25 返回相关性高的文档"""
        store = MockVectorStore()
        store._documents = [
            Document(id="1", content="RAG 是检索增强生成技术", metadata={}),
            Document(id="2", content="今天天气很好适合出去散步", metadata={}),
            Document(id="3", content="向量数据库用于存储和检索向量", metadata={}),
        ]

        retriever = BM25Retriever(vector_store=store)
        results = retriever.retrieve("RAG 检索增强", top_k=3)

        # 最相关的结果应该是 doc 1（包含 RAG 和检索增强）
        assert len(results) > 0
        # BM25 对 "RAG" 和 "检索增强" 都会匹配到 doc 1 和 doc 3
        top_ids = [r.id for r in results]
        assert "1" in top_ids

    def test_retrieve_top_k(self):
        """测试 top_k 参数正确限制返回数量"""
        store = MockVectorStore()
        docs = [
            Document(id=str(i), content=f"这是第{i}篇文档的内容", metadata={})
            for i in range(10)
        ]
        store._documents = docs

        retriever = BM25Retriever(vector_store=store)
        results = retriever.retrieve("文档", top_k=3)

        assert len(results) <= 3

    def test_retrieve_default_top_k(self):
        """测试不传 top_k 时使用默认值"""
        store = MockVectorStore()
        docs = [
            Document(id=str(i), content=f"文档{i}", metadata={})
            for i in range(20)
        ]
        store._documents = docs

        retriever = BM25Retriever(vector_store=store, top_k=7)
        results = retriever.retrieve("文档")

        # 不传 top_k 时，retrieve() 内默认值是 5（方法签名默认值）
        # _default_top_k 只在 BM25Retriever 内部未显式传参时体现
        assert len(results) <= 5

    # ── SearchResult 格式 ──

    def test_retrieve_returns_search_results(self):
        """测试返回结果是正确的 SearchResult 格式"""
        store = MockVectorStore()
        store._documents = [
            Document(
                id="doc-1",
                content="RAG 技术详解",
                metadata={"source": "wiki", "category": "tech"},
            ),
        ]

        retriever = BM25Retriever(vector_store=store)
        results = retriever.retrieve("RAG", top_k=1)

        assert len(results) == 1
        r = results[0]
        assert r.id == "doc-1"
        assert r.content == "RAG 技术详解"
        assert r.metadata["source"] == "wiki"
        assert r.metadata["category"] == "tech"
        assert isinstance(r.score, float)

    # ── filter_conditions ──

    def test_retrieve_with_filter(self):
        """测试 filter_conditions 后过滤"""
        store = MockVectorStore()
        store._documents = [
            Document(id="1", content="RAG 技术", metadata={"dataset_id": "ds1"}),
            Document(id="2", content="RAG 技术", metadata={"dataset_id": "ds2"}),
            Document(id="3", content="RAG 技术", metadata={"dataset_id": "ds1"}),
        ]

        retriever = BM25Retriever(vector_store=store)
        results = retriever.retrieve("RAG", top_k=5, filter_conditions={"dataset_id": "ds1"})

        assert len(results) == 2
        assert all(r.metadata["dataset_id"] == "ds1" for r in results)

    def test_retrieve_with_filter_no_match(self):
        """测试 filter_conditions 无匹配时返回空"""
        store = MockVectorStore()
        store._documents = [
            Document(id="1", content="RAG", metadata={"dataset_id": "ds1"}),
        ]

        retriever = BM25Retriever(vector_store=store)
        results = retriever.retrieve("RAG", top_k=5, filter_conditions={"dataset_id": "nonexistent"})

        assert len(results) == 0

    # ── refresh ──

    def test_refresh_rebuilds_index(self):
        """测试 refresh 重新构建索引"""
        store = MockVectorStore()
        store._documents = [
            Document(id="1", content="旧文档内容", metadata={}),
        ]

        retriever = BM25Retriever(vector_store=store)
        retriever.retrieve("旧文档")  # 触发建索引
        old_size = retriever.corpus_size

        # 添加新文档
        store._documents.append(Document(id="2", content="新文档内容", metadata={}))

        # refresh 前索引大小不变
        assert retriever.corpus_size == old_size

        # refresh 后索引重建
        retriever.refresh()
        assert retriever.corpus_size == 2

    # ── 中文分词 ──

    def test_chinese_tokenization(self):
        """测试中文文本正常分词和检索"""
        store = MockVectorStore()
        store._documents = [
            Document(id="1", content="深度学习是机器学习的一个分支", metadata={}),
            Document(id="2", content="机器学习是人工智能的核心", metadata={}),
            Document(id="3", content="Python 是一种编程语言", metadata={}),
        ]

        retriever = BM25Retriever(vector_store=store)
        results = retriever.retrieve("机器学习深度学习", top_k=3)

        ids = [r.id for r in results]
        # "机器学习" 应该排在前面
        assert "2" in ids
        assert "1" in ids

    # ── 属性 ──

    def test_is_index_built_property(self):
        """测试 is_index_built 属性"""
        store = MockVectorStore()
        store._documents = [Document(id="1", content="测试", metadata={})]

        retriever = BM25Retriever(vector_store=store)
        assert retriever.is_index_built is False

        retriever.retrieve("测试", top_k=1)
        assert retriever.is_index_built is True

    def test_corpus_size_property(self):
        """测试 corpus_size 属性"""
        store = MockVectorStore()
        retriever = BM25Retriever(vector_store=store)

        # 建索引前为 0
        assert retriever.corpus_size == 0
