# M23：DI 容器模块 (core/container)

**阶段**: Phase 6 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: 所有模块（M01-M22）

**参考设计**: [详细设计文档 Module-23](../详细设计文档.md#module-23-依赖注入容器-corecontainer)

---

## 任务清单

### 1. Container 类

- [ ] 创建 `backend/app/core/container.py`
  - [ ] `Container` 类
  - [ ] `__init__(settings: Settings)` — 初始化所有基础设施
    - [ ] `_database` — DatabaseManager
    - [ ] `_security` — SecurityManager
    - [ ] `_storage` — 根据配置创建 FileStorageBackend
    - [ ] `_task_queue` — 根据配置创建 TaskQueueBackend
  - [ ] RAG 组件（懒加载 @property）
    - [ ] `parser_router` — 创建并注册默认解析器
    - [ ] `splitter` — FixedSizeSplitter（从配置读取参数）
    - [ ] `embedding` — 根据配置创建 EmbeddingBackend
    - [ ] `vector_store` — 根据配置创建 VectorStore
    - [ ] `llm` — 根据配置创建 LLMBackend
    - [ ] `retriever` — VectorRetriever（组合 embedding + vector_store）
    - [ ] `pipeline` — DocumentPipeline
    - [ ] `rag_engine` — RAGEngine（组合 retriever + llm）
  - [ ] 业务服务（懒加载 @property）
    - [ ] `user_service` — 注入 database + security
    - [ ] `dataset_service` — 注入 database
    - [ ] `document_service` — 注入 database + storage + task_queue + pipeline
    - [ ] `conversation_service` — 注入 database + rag_engine
    - [ ] `admin_service` — 注入 database
  - [ ] 生命周期管理
    - [ ] `async initialize()` — 初始化 database
    - [ ] `async close()` — 关闭 database
  - [ ] `static async get()` — FastAPI Depends 工厂方法

### 2. 存储后端选择逻辑

- [ ] `_create_storage()`:
  - `local` → LocalFileStorage
  - `s3` → NotImplementedError（预留）
  - 其他 → ValueError

### 3. 任务队列选择逻辑

- [ ] `_create_task_queue()`:
  - `huey` → HueyTaskQueue
  - `celery` → NotImplementedError（预留）
  - `arq` → NotImplementedError（预留）
  - 其他 → ValueError

### 4. 测试

- [ ] 创建 `backend/app/core/tests/test_container.py`
  - [ ] 使用测试 Settings 创建 Container
  - [ ] 验证所有属性可访问（不为 None）
  - [ ] 验证懒加载（访问前不初始化）
  - [ ] 验证生命周期方法可调用

### 5. 验证

- [ ] Container 可正常创建所有组件
- [ ] 配置变更正确影响组件选择
- [ ] `pytest backend/app/core/tests/test_container.py` 全部通过

---

## 验收标准

- [ ] Container 不包含任何业务逻辑（纯组装）
- [ ] 所有组件通过属性访问（非方法调用）
- [ ] 组件懒加载（按需初始化）
- [ ] `initialize()` 和 `close()` 生命周期完整
- [ ] 配置驱动的组件切换
