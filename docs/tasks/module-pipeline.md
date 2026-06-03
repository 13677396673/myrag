# M15：文档处理管道模块 (rag/pipeline)

**阶段**: Phase 4 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M08 Interfaces、M09 Parsers、M10 Splitters、M11 Embedding、M12 VectorStore

**参考设计**: [详细设计文档 Module-15](../详细设计文档.md#module-15-文档处理管道模块-ragpipeline)

---

## 任务清单

### 1. DocumentPipeline

- [ ] 创建 `backend/app/rag/pipeline.py`
  - [ ] `DocumentPipeline` 类
  - [ ] `__init__(parser_router, splitter, embedding, vector_store)`
  - [ ] `process_document(file_path, document_id, user_id, dataset_id) -> int`
    - [ ] Step 1: 根据文件扩展名从 ParserRouter 获取解析器
      - [ ] 不支持格式 → 抛出 `ValueError`
    - [ ] Step 2: 调用 parser.parse(file_path)
    - [ ] Step 3: 调用 splitter.split(content, metadata)
    - [ ] Step 4: 调用 embedding.embed_documents(texts)
    - [ ] Step 5: 调用 vector_store.add_embeddings(ids, vectors, metadatas)
    - [ ] Step 6: 返回 chunk 数量
  - [ ] chunk ID 格式：`{document_id}_{chunk_index}`

### 2. 测试

- [ ] 创建 `backend/app/rag/tests/__init__.py`
- [ ] 创建 `backend/app/rag/tests/test_pipeline.py`
  - [ ] Mock `ParserRouter`
  - [ ] Mock `TextSplitter`
  - [ ] Mock `EmbeddingBackend`
  - [ ] Mock `VectorStore`
  - [ ] 测试完整流程：解析 → 切片 → Embedding → 存储
  - [ ] 验证调用顺序正确
  - [ ] 测试不支持的文件格式 → 抛出 ValueError
  - [ ] 测试空文档（返回 0）
- [ ] 创建 `backend/app/rag/tests/conftest.py`
  - [ ] Fixture：所有 Mock 组件
  - [ ] Fixture：DocumentPipeline 实例

### 3. 验证

- [ ] Pipeline 编排正确
- [ ] 各组件调用顺序符合设计
- [ ] `pytest backend/app/rag/tests/test_pipeline.py` 全部通过

---

## 验收标准

- [ ] Pipeline 不包含任何实现细节（只编排）
- [ ] 每个步骤间的数据传递类型正确
- [ ] 错误传播清晰（解析失败 → 抛出异常）
- [ ] 返回切片数量
