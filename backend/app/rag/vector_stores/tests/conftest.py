"""pytest fixtures for vector store tests"""

import gc
import tempfile
from typing import List, Dict, Any

import pytest

from app.rag.vector_stores import ChromaDBStore


@pytest.fixture
def chroma_store():
    """提供使用临时目录的 ChromaDBStore 实例"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        store = ChromaDBStore(persist_directory=tmpdir)
        yield store
        # 手动清理 ChromaDB 的客户端，释放文件锁（Windows 需要）
        del store
        gc.collect()


@pytest.fixture
def sample_embeddings_data():
    """提供测试用的向量数据和元数据

    返回 (ids, vectors, metadatas) 三元组：
    - ids: 3 个向量 ID
    - vectors: 3 条 4 维向量
    - metadatas: 对应的元数据（含 dataset_id / user_id / tags 等）
    """
    ids = ["vec_1", "vec_2", "vec_3"]
    vectors = [
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8],
        [0.9, 0.1, 0.2, 0.3],
    ]
    metadatas: List[Dict[str, Any]] = [
        {"dataset_id": "ds1", "user_id": "u1", "page": 1, "tags": ["intro", "overview"]},
        {"dataset_id": "ds1", "user_id": "u1", "page": 2, "nested": {"key": "val"}},
        {"dataset_id": "ds2", "user_id": "u2", "page": 1},
    ]
    return ids, vectors, metadatas
