# M14：检索器模块 (rag/retrievers)

**阶段**: Phase 3 | **优先级**: P1 | **状态**: 🔲 未开始

**依赖模块**: M08 Interfaces（EmbeddingBackend、VectorStore）

**参考设计**: [详细设计文档 Module-14](../详细设计文档.md#module-14-检索器模块-ragretrievers)

---

## 任务清单

### 1. VectorRetriever

- [ ] 创建 `backend/app/rag/retrievers/__init__.py`
- [ ] 创建 `backend/app/rag/retrievers/vector_retriever.py`
  - [ ] `VectorRetriever(Retriever)`
  - [ ] `__init__(embedding: EmbeddingBackend, vector_store: VectorStore)`
  - [ ] `retrieve(query, top_k, filter_conditions) -> List[SearchResult]`
    - [ ] 调用 `embedding.embed_text(query)` 转为向量
    - [ ] 调用 `vector_store.search(query_vector, top_k, filter_conditions)` 搜索
    - [ ] 透传 filter_conditions

### 2. 预留检索器

- [ ] 创建 `backend/app/rag/retrievers/hybrid_retriever.py`（占位）
- [ ] 创建 `backend/app/rag/retrievers/bm25_retriever.py`（占位）

### 3. 测试

- [ ] 创建 `backend/app/rag/retrievers/tests/__init__.py`
- [ ] 创建 `backend/app/rag/retrievers/tests/test_vector_retriever.py`
  - [ ] Mock `EmbeddingBackend`（返回固定向量）
  - [ ] Mock `VectorStore`（返回固定结果）
  - [ ] 测试 retrieve 正确调用了 embed_text → search
  - [ ] 测试 filter_conditions 透传
  - [ ] 测试 top_k 参数传递

### 4. 验证

- [ ] `pytest backend/app/rag/retrievers/tests/` 全部通过

---

## 验收标准

- [ ] 检索器通过依赖注入组合 Embedding 和 VectorStore
- [ ] 无业务逻辑（Service 层负责拼 filter_conditions）
- [ ] 纯"编排"角色，可独立测试
