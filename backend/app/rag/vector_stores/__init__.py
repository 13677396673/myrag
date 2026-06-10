"""向量存储模块

提供 ``ChromaDBStore``（本地嵌入式向量数据库）实现，
以及 FAISS / Milvus / PGVector 占位类供后续扩展。

用法::

    from app.rag.vector_stores import ChromaDBStore

    store = ChromaDBStore(persist_directory="./data/chromadb")
    store.add_embeddings(ids=["1"], vectors=[[0.1, 0.2]], metadatas=[{"key": "val"}])
"""

from .chromadb_store import ChromaDBStore

__all__ = [
    "ChromaDBStore",
]
