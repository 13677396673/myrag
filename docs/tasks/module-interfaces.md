# M08：RAG 抽象接口模块 (rag/interfaces)

**阶段**: Phase 2 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: 无（完全独立）

**参考设计**: [详细设计文档 Module-08](../详细设计文档.md#module-08-rag-抽象接口模块-raginterfaces)

---

## 任务清单

### 1. DocumentParser 接口

- [ ] 创建 `backend/app/rag/__init__.py`
- [ ] 创建 `backend/app/rag/interfaces/__init__.py`
- [ ] 创建 `backend/app/rag/interfaces/parser.py`
  - [ ] `ParsedDocument` dataclass — content、metadata、sections
  - [ ] `DocumentParser` 抽象类
  - [ ] `parse(file_path: str) -> ParsedDocument` 抽象方法
  - [ ] `supported_extensions() -> List[str]` 抽象类方法

### 2. TextSplitter 接口

- [ ] 创建 `backend/app/rag/interfaces/splitter.py`
  - [ ] `DocumentChunk` dataclass — content、chunk_index、metadata
  - [ ] `TextSplitter` 抽象类
  - [ ] `split(text: str, metadata: Optional[dict]) -> List[DocumentChunk]` 抽象方法
  - [ ] `type_name -> str` 抽象属性

### 3. EmbeddingBackend 接口

- [ ] 创建 `backend/app/rag/interfaces/embedding.py`
  - [ ] `EmbeddingBackend` 抽象类
  - [ ] `embed_text(text: str) -> List[float]` 抽象方法
  - [ ] `embed_documents(texts: List[str]) -> List[List[float]]` 抽象方法
  - [ ] `dimension -> int` 抽象属性

### 4. VectorStore 接口

- [ ] 创建 `backend/app/rag/interfaces/vector_store.py`
  - [ ] `SearchResult` dataclass — id、score、metadata、content(可选)
  - [ ] `VectorStore` 抽象类
  - [ ] `add_embeddings(ids, vectors, metadatas)` 抽象方法
  - [ ] `search(query_vector, top_k, filter_conditions) -> List[SearchResult]` 抽象方法
  - [ ] `delete(ids)` 抽象方法
  - [ ] `delete_by_metadata(filter_conditions) -> int` 抽象方法
  - [ ] `count(filter_conditions) -> int` 抽象方法

### 5. LLMBackend 接口

- [ ] 创建 `backend/app/rag/interfaces/llm.py`
  - [ ] `LLMBackend` 抽象类
  - [ ] `async generate(messages, temperature, max_tokens) -> str` 抽象方法
  - [ ] `async generate_stream(messages, temperature, max_tokens) -> AsyncIterator[str]` 抽象方法
  - [ ] `model_name -> str` 抽象属性

### 6. Retriever 接口

- [ ] 创建 `backend/app/rag/interfaces/retriever.py`
  - [ ] `Retriever` 抽象类
  - [ ] `retrieve(query, top_k, filter_conditions) -> List[SearchResult]` 抽象方法

### 7. interfaces/\_\_init\_\_.py

- [ ] 导出所有接口类和 dataclass

### 8. 测试

- [ ] 创建 `backend/app/rag/interfaces/tests/__init__.py`
- [ ] 创建 `backend/app/rag/interfaces/tests/test_interfaces.py`
  - [ ] 验证所有抽象类不能直接实例化
  - [ ] 验证 Mock 实现类可以正确调用所有方法
  - [ ] 验证 dataclass 的默认值
  - [ ] 验证接口方法的参数签名正确

### 9. 验证

- [ ] 接口定义与详细设计文档完全一致
- [ ] 所有抽象方法签名正确
- [ ] `pytest backend/app/rag/interfaces/tests/` 全部通过

---

## 验收标准

- [ ] 6 个核心接口定义完整、方法签名正确
- [ ] 接口不含任何业务实现代码
- [ ] Type hints 齐全
- [ ] 所有接口使用抽象类 + `@abstractmethod`
