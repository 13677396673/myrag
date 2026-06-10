# M11：Embedding 模块 (rag/embeddings)

**阶段**: Phase 3 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M01 Config、M08 Interfaces

**参考设计**: [详细设计文档 Module-11](../详细设计文档.md#module-11-embedding-模块-ragembeddings)

---

## 任务清单

### 1. BGESmallEmbedding

- [x] 创建 `backend/app/rag/embeddings/__init__.py`
- [x] 创建 `backend/app/rag/embeddings/bge_embedding.py`
  - [x] `BGESmallEmbedding(EmbeddingBackend)`
  - [x] `__init__(model_name, device="cpu")`
  - [x] `_load_model()` — 使用 `sentence-transformers` 加载模型
  - [x] `embed_text(text) -> List[float]`
  - [x] `embed_documents(texts) -> List[List[float]]`
  - [x] `dimension -> 384`

### 2. OpenAIEmbedding

- [x] 创建 `backend/app/rag/embeddings/openai_embedding.py`
  - [x] `OpenAIEmbedding(EmbeddingBackend)`
  - [x] `__init__(api_key, model="text-embedding-3-small")`
  - [x] `embed_text(text)` — 调用 OpenAI API
  - [x] `embed_documents(texts)` — 批量调用并按输入顺序排序
  - [x] `dimension -> 1536`

### 3. 注册工厂函数（可选）

- [x] 在 `embeddings/__init__.py` 中定义 `create_embedding(settings: Settings) -> EmbeddingBackend`
  - [x] 根据 `settings.EMBEDDING_BACKEND` 选择实现
  - [x] 支持 `bge-small` 和 `openai`

### 4. 测试

- [x] 创建 `backend/app/rag/embeddings/tests/__init__.py`
- [x] 创建 `backend/app/rag/embeddings/tests/test_bge_embedding.py`
  - [x] 使用 mock 替换 `SentenceTransformer`（单元测试不下载真实模型）
  - [x] 测试 `embed_text` 返回 List[float] 且维度 = 384
  - [x] 测试 `embed_documents` 批量返回
  - [x] 测试 `dimension` 属性
- [x] 创建 `backend/app/rag/embeddings/tests/test_openai_embedding.py`
  - [x] 使用 `pytest-httpx` 或 mock 替换 `openai` 客户端
  - [x] 测试 embed_text 返回正确的维度
  - [x] 测试 embed_documents 的排序

### 5. 验证

- [x] `bge-small-zh-v1.5` 可正常下载和加载（首次运行）
- [x] 嵌入向量维度一致
- [x] `pytest backend/app/rag/embeddings/tests/` 全部通过

---

## 验收标准

- [x] BGE-small-zh-v1.5 本地模型可用（HTTP 资源占用验证通过）
- [x] OpenAI Embedding 兼容
- [x] 向量维度正确（384 / 1536）
- [x] 单条和批量接口均可用
- [x] 接口实现可替换
