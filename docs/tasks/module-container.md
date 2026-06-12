# M23：DI 容器模块 (core/container)

**阶段**: Phase 6 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: 所有模块（M01-M22）

**参考设计**: [详细设计文档 Module-23](../详细设计文档.md#module-23-依赖注入容器-corecontainer)

---

## 任务清单

### 1. Container 类

- [x] 创建 `backend/app/core/container.py`
  - [x] `Container` 类
  - [x] `__init__(settings: Settings)` — 初始化所有基础设施
    - [x] `_database` — DatabaseManager
    - [x] `_security` — SecurityManager
    - [x] `_storage` — 根据配置创建 FileStorageBackend
    - [x] `_task_queue` — 根据配置创建 TaskQueueBackend
  - [x] RAG 组件（懒加载 @property）
    - [x] `parser_router` — 创建并注册默认解析器
    - [x] `splitter` — FixedSizeSplitter（从配置读取参数）
    - [x] `embedding` — 根据配置创建 EmbeddingBackend
    - [x] `vector_store` — 根据配置创建 VectorStore
    - [x] `llm` — 根据配置创建 LLMBackend
    - [x] `retriever` — VectorRetriever（组合 embedding + vector_store）
    - [x] `pipeline` — DocumentPipeline
    - [x] `rag_engine` — RAGEngine（组合 retriever + llm）
  - [x] 业务服务（懒加载 @property）
    - [x] `user_service` — 注入 database + security
    - [x] `dataset_service` — 注入 database
    - [x] `document_service` — 注入 database + storage + task_queue + pipeline
    - [x] `conversation_service` — 注入 database + rag_engine
    - [x] `admin_service` — 注入 database
  - [x] 生命周期管理
    - [x] `async initialize()` — 初始化 database
    - [x] `async close()` — 关闭 database
  - [x] `static async get()` — FastAPI Depends 工厂方法

### 2. 存储后端选择逻辑

- [x] `_create_storage()`:
  - `local` → LocalFileStorage
  - `s3` → NotImplementedError（预留）
  - 其他 → ValueError

### 3. 任务队列选择逻辑

- [x] `_create_task_queue()`:
  - `huey` → HueyTaskQueue
  - `celery` → NotImplementedError（预留）
  - `arq` → NotImplementedError（预留）
  - 其他 → ValueError

### 4. 测试

- [x] 创建 `backend/app/core/tests/test_container.py`
  - [x] 使用测试 Settings 创建 Container
  - [x] 验证所有属性可访问（不为 None）
  - [x] 验证懒加载（访问前不初始化）
  - [x] 验证生命周期方法可调用

### 5. 验证

- [x] Container 可正常创建所有组件
- [x] 配置变更正确影响组件选择
- [x] `pytest backend/app/core/tests/test_container.py` 全部通过

---

## 验收标准

- [x] Container 不包含任何业务逻辑（纯组装）
- [x] 所有组件通过属性访问（非方法调用）
- [x] 组件懒加载（按需初始化）
- [x] `initialize()` 和 `close()` 生命周期完整
- [x] 配置驱动的组件切换
