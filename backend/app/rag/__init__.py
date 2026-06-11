"""
RAG 模块 — 包含所有 RAG 核心接口、组件实现和编排逻辑。
"""

from .interfaces import (
    DocumentParser,
    ParsedDocument,
    TextSplitter,
    DocumentChunk,
    EmbeddingBackend,
    VectorStore,
    SearchResult,
    LLMBackend,
    Retriever,
)
from .rag_engine import RAGEngine

__all__ = [
    "DocumentParser",
    "ParsedDocument",
    "TextSplitter",
    "DocumentChunk",
    "EmbeddingBackend",
    "VectorStore",
    "SearchResult",
    "LLMBackend",
    "Retriever",
    "RAGEngine",
]
