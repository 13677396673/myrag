# M11：Embedding 模块 (rag/embeddings)

**阶段**: Phase 3 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M01 Config、M08 Interfaces

**参考设计**: [详细设计文档 Module-11](../详细设计文档.md#module-11-embedding-模块-ragembeddings)

---

## 任务清单

### 1. BGESmallEmbedding

- [ ] 创建 `backend/app/rag/embeddings/__init__.py`
- [ ] 创建 `backend/app/rag/embeddings/bge_embedding.py`
  - [ ] `BGESmallEmbedding(EmbeddingBackend)`
  - [ ] `__init__(model_name, device="cpu")`
  - [ ] `_load_model()` — 使用 `sentence-transformers` 加载模型
  - [ ] `embed_text(text) -> List[float]`
  - [ ] `embed_documents(texts) -> List[List[float]]`
  - [ ] `dimension -> 384`

### 2. OpenAIEmbedding

- [ ] 创建 `backend/app/rag/embeddings/openai_embedding.py`
  - [ ] `OpenAIEmbedding(EmbeddingBackend)`
  - [ ] `__init__(api_key, model="text-embedding-3-small")`
  - [ ] `embed_text(text)` — 调用 OpenAI API
  - [ ] `embed_documents(texts)` — 批量调用并按输入顺序排序
  - [ ] `dimension -> 1536`

### 3. 注册工厂函数（可选）

- [ ] 在 `embeddings/__init__.py` 中定义 `create_embedding(settings: Settings) -> EmbeddingBackend`
  - [ ] 根据 `settings.EMBEDDING_BACKEND` 选择实现
  - [ ] 支持 `bge-small` 和 `openai`

### 4. 测试

- [ ] 创建 `backend/app/rag/embeddings/tests/__init__.py`
- [ ] 创建 `backend/app/rag/embeddings/tests/test_bge_embedding.py`
  - [ ] 使用 mock 替换 `SentenceTransformer`（单元测试不下载真实模型）
  - [ ] 测试 `embed_text` 返回 List[float] 且维度 = 384
  - [ ] 测试 `embed_documents` 批量返回
  - [ ] 测试 `dimension` 属性
- [ ] 创建 `backend/app/rag/embeddings/tests/test_openai_embedding.py`
  - [ ] 使用 `pytest-httpx` 或 mock 替换 `openai` 客户端
  - [ ] 测试 embed_text 返回正确的维度
  - [ ] 测试 embed_documents 的排序

### 5. 验证

- [ ] `bge-small-zh-v1.5` 可正常下载和加载（首次运行）
- [ ] 嵌入向量维度一致
- [ ] `pytest backend/app/rag/embeddings/tests/` 全部通过

---

## 验收标准

- [ ] BGE-small-zh-v1.5 本地模型可用（HTTP 资源占用验证通过）
- [ ] OpenAI Embedding 兼容
- [ ] 向量维度正确（384 / 1536）
- [ ] 单条和批量接口均可用
- [ ] 接口实现可替换
