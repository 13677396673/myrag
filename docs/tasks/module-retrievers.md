# M14：检索器模块 (rag/retrievers)

**阶段**: Phase 3 | **优先级**: P1 | **状态**: ✅ 已完成

**依赖模块**: M08 Interfaces（EmbeddingBackend、VectorStore）

**参考设计**: [详细设计文档 Module-14](../详细设计文档.md#module-14-检索器模块-ragretrievers)

---

## 任务清单

### 1. VectorRetriever

- [x] 创建 `backend/app/rag/retrievers/__init__.py`
- [x] 创建 `backend/app/rag/retrievers/vector_retriever.py`
  - [x] `VectorRetriever(Retriever)`
  - [x] `__init__(embedding: EmbeddingBackend, vector_store: VectorStore)`
  - [x] `retrieve(query, top_k, filter_conditions) -> List[SearchResult]`
    - [x] 调用 `embedding.embed_text(query)` 转为向量
    - [x] 调用 `vector_store.search(query_vector, top_k, filter_conditions)` 搜索
    - [x] 透传 filter_conditions

### 2. 预留检索器

- [x] 创建 `backend/app/rag/retrievers/hybrid_retriever.py`（占位）
- [x] 创建 `backend/app/rag/retrievers/bm25_retriever.py`（占位）

### 3. 测试

- [x] 创建 `backend/app/rag/retrievers/tests/__init__.py`
- [x] 创建 `backend/app/rag/retrievers/tests/test_vector_retriever.py`
  - [x] Mock `EmbeddingBackend`（返回固定向量）
  - [x] Mock `VectorStore`（返回固定结果）
  - [x] 测试 retrieve 正确调用了 embed_text → search
  - [x] 测试 filter_conditions 透传
  - [x] 测试 top_k 参数传递

### 4. 验证

- [x] `pytest backend/app/rag/retrievers/tests/` 全部通过

---

## 验收标准

- [x] 检索器通过依赖注入组合 Embedding 和 VectorStore
- [x] 无业务逻辑（Service 层负责拼 filter_conditions）
- [x] 纯"编排"角色，可独立测试
