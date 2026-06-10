"""Tests for M12: ChromaDBStore (rag/vector_stores)

验证内容：
1. 添加向量 → 搜索找到结果
2. 添加后删除 → 搜索不到
3. filter_conditions 过滤
4. count 方法
5. metadata 中包含 dict/list 类型值时的兼容处理
6. 空 store 搜索返回空列表
7. delete_by_metadata 按条件删除
"""

import pytest

from app.rag.interfaces.vector_store import SearchResult


# =========================================================================
# Test: 基本添加和搜索
# =========================================================================

class TestAddAndSearch:
    """验证添加向量后能搜索到结果"""

    def test_add_and_search_finds_results(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        results = chroma_store.search(query_vector=[0.1, 0.2, 0.3, 0.4], top_k=3)
        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        assert results[0].id in ids

    def test_search_returns_correct_count(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        results = chroma_store.search(query_vector=[0.0] * 4, top_k=2)
        assert len(results) == 2

    def test_search_returns_search_result_fields(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        results = chroma_store.search(query_vector=[0.1, 0.2, 0.3, 0.4], top_k=1)
        assert len(results) == 1
        assert isinstance(results[0].id, str)
        assert isinstance(results[0].score, float)
        assert isinstance(results[0].metadata, dict)


# =========================================================================
# Test: 删除
# =========================================================================

class TestDelete:
    """验证删除功能"""

    def test_delete_removes_vectors(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        chroma_store.delete(ids=["vec_1"])
        results = chroma_store.search(query_vector=[0.0] * 4, top_k=10)
        result_ids = [r.id for r in results]
        assert "vec_1" not in result_ids
        assert len(result_ids) == 2

    def test_delete_nonexistent_id_does_not_raise(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        # 删除不存在的 ID 不应抛出异常
        chroma_store.delete(ids=["nonexistent_id"])
        assert chroma_store.count() == 3

    def test_delete_by_metadata(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        deleted = chroma_store.delete_by_metadata({"dataset_id": "ds1"})
        assert deleted == 2
        assert chroma_store.count() == 1

    def test_delete_by_metadata_no_match(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        deleted = chroma_store.delete_by_metadata({"dataset_id": "nonexistent"})
        assert deleted == 0
        assert chroma_store.count() == 3


# =========================================================================
# Test: 过滤条件搜索
# =========================================================================

class TestSearchWithFilter:
    """验证 filter_conditions 过滤"""

    def test_filter_by_dataset_id(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        results = chroma_store.search(
            query_vector=[0.0] * 4,
            top_k=10,
            filter_conditions={"dataset_id": "ds1"},
        )
        assert len(results) == 2

    def test_filter_by_user_id(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        results = chroma_store.search(
            query_vector=[0.0] * 4,
            top_k=10,
            filter_conditions={"user_id": "u2"},
        )
        assert len(results) == 1

    def test_filter_no_match_returns_empty(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        results = chroma_store.search(
            query_vector=[0.0] * 4,
            top_k=10,
            filter_conditions={"dataset_id": "nonexistent"},
        )
        assert len(results) == 0

    def test_filter_without_filter_returns_all(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        results = chroma_store.search(query_vector=[0.0] * 4, top_k=10)
        assert len(results) == 3


# =========================================================================
# Test: Count
# =========================================================================

class TestCount:
    """验证 count 方法"""

    def test_count_total(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)
        assert chroma_store.count() == 3

    def test_count_with_filter(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)
        assert chroma_store.count(filter_conditions={"dataset_id": "ds1"}) == 2
        assert chroma_store.count(filter_conditions={"dataset_id": "ds2"}) == 1

    def test_count_empty_store(self, chroma_store):
        assert chroma_store.count() == 0

    def test_count_after_delete(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)
        chroma_store.delete(["vec_1"])
        assert chroma_store.count() == 2


# =========================================================================
# Test: Metadata 清理
# =========================================================================

class TestMetadataSanitization:
    """验证 metadata 中的 dict/list 类型值被自动转为 string"""

    def test_list_in_metadata(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        # vec_1 的 tags 是 list，应被转为 string
        results = chroma_store.search(
            query_vector=[0.1, 0.2, 0.3, 0.4],
            top_k=1,
        )
        assert len(results) > 0
        # tags 字段应该是字符串
        result_meta = results[0].metadata
        if "tags" in result_meta:
            assert isinstance(result_meta["tags"], str)

    def test_dict_in_metadata(self, chroma_store, sample_embeddings_data):
        ids, vectors, metadatas = sample_embeddings_data
        chroma_store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

        # vec_2 的 nested 是 dict，应被转为 string
        results = chroma_store.search(
            query_vector=[0.5, 0.6, 0.7, 0.8],
            top_k=1,
        )
        assert len(results) > 0
        result_meta = results[0].metadata
        if "nested" in result_meta:
            assert isinstance(result_meta["nested"], str)

    def test_simple_types_preserved(self, chroma_store):
        """验证基本类型（str/int/float/bool）不被转换"""
        store = chroma_store
        store.add_embeddings(
            ids=["test"],
            vectors=[[0.1, 0.2, 0.3, 0.4]],
            metadatas=[{
                "string": "hello",
                "int_val": 42,
                "float_val": 3.14,
                "bool_val": True,
            }],
        )
        results = store.search(query_vector=[0.1, 0.2, 0.3, 0.4], top_k=1)
        assert len(results) == 1
        meta = results[0].metadata
        assert meta["string"] == "hello"
        assert meta["int_val"] == 42
        assert meta["float_val"] == 3.14
        assert meta["bool_val"] is True


# =========================================================================
# Test: 空 Store
# =========================================================================

class TestEmptyStore:
    """验证空 store 的行为"""

    def test_search_empty_returns_empty_list(self, chroma_store):
        results = chroma_store.search(query_vector=[0.0] * 4, top_k=5)
        assert results == []

    def test_count_empty_is_zero(self, chroma_store):
        assert chroma_store.count() == 0

    def test_delete_empty_does_not_raise(self, chroma_store):
        chroma_store.delete(ids=["nonexistent"])

    def test_delete_by_metadata_empty_returns_zero(self, chroma_store):
        deleted = chroma_store.delete_by_metadata({"dataset_id": "ds1"})
        assert deleted == 0
