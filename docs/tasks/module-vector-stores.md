# M12：向量存储模块 (rag/vector_stores)

**阶段**: Phase 3 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M01 Config、M08 Interfaces

**参考设计**: [详细设计文档 Module-12](../详细设计文档.md#module-12-向量存储模块-ragvector_stores)

---

## 任务清单

### 1. ChromaDBStore

- [ ] 创建 `backend/app/rag/vector_stores/__init__.py`
- [ ] 创建 `backend/app/rag/vector_stores/chromadb_store.py`
  - [ ] `ChromaDBStore(VectorStore)`
  - [ ] `__init__(persist_directory, collection_name="documents")`
    - [ ] 初始化 `PersistentClient`
    - [ ] 使用 cosine 距离
  - [ ] `add_embeddings(ids, vectors, metadatas)` — 添加时清理元数据（dict/list 转 string）
  - [ ] `search(query_vector, top_k, filter_conditions)` — 查询并返回 SearchResult
  - [ ] `delete(ids)` — 按 ID 删除
  - [ ] `delete_by_metadata(filter_conditions)` — 按条件查询后删除
  - [ ] `count(filter_conditions)` — 计数

### 2. 预留向量库

- [ ] 创建 `backend/app/rag/vector_stores/faiss_store.py`（占位）
- [ ] 创建 `backend/app/rag/vector_stores/milvus_store.py`（占位）
- [ ] 创建 `backend/app/rag/vector_stores/pgvector_store.py`（占位）

### 3. 测试

- [ ] 创建 `backend/app/rag/vector_stores/tests/__init__.py`
- [ ] 创建 `backend/app/rag/vector_stores/tests/test_chromadb_store.py`
  - [ ] 使用临时目录（`tempfile.TemporaryDirectory`）做持久化路径
  - [ ] 测试添加向量 → 搜索找到结果
  - [ ] 测试添加后删除 → 搜索不到
  - [ ] 测试 filter_conditions 过滤
  - [ ] 测试 count
  - [ ] 测试 metadata 中包含 dict/list 类型值时的兼容处理
  - [ ] 测试空 store 搜索返回空列表
- [ ] 创建 `backend/app/rag/vector_stores/tests/conftest.py`
  - [ ] Fixture：临时目录的 ChromaDBStore
  - [ ] Fixture：测试用的向量数据和元数据

### 4. 验证

- [ ] ChromaDB 可正常运行（需安装 chromadb）
- [ ] 搜索、添加、删除流程完整
- [ ] 过滤条件工作正常
- [ ] `pytest backend/app/rag/vector_stores/tests/` 全部通过

---

## 验收标准

- [ ] ChromaDB 完整 CRUD 操作通过测试
- [ ] 向量维度与 Embedding 模块匹配（384）
- [ ] 过滤条件（user_id、dataset_id）正常工作
- [ ] metadata 中的非法类型被自动清理
