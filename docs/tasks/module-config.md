# M01：配置管理模块 (config)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: 无（完全独立）

**参考设计**: [详细设计文档 Module-01](../详细设计文档.md#module-01-配置管理模块-config)

---

## 任务清单

### 1. Settings 类

- [x] 创建 `backend/app/config/__init__.py`
- [x] 创建 `backend/app/config/settings.py`
  - [x] 定义 `Settings` 类（继承 `pydantic-settings.BaseSettings`）
  - [x] 应用基础配置：`APP_NAME`、`APP_VERSION`、`APP_DEBUG`
  - [x] 服务配置：`SERVER_HOST`、`SERVER_PORT`、`SERVER_CORS_ORIGINS`
  - [x] 数据库配置：`DATABASE_URL`、`DATABASE_ECHO`
  - [x] JWT 配置：`JWT_SECRET_KEY`、`JWT_ALGORITHM`、`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
  - [x] 文件存储配置：`STORAGE_BACKEND`、`STORAGE_LOCAL_PATH`、`STORAGE_MAX_FILE_SIZE`、`STORAGE_S3_*`
  - [x] 任务队列配置：`TASK_QUEUE_BACKEND`、`TASK_QUEUE_REDIS_URL`
  - [x] LLM 配置：`LLM_BACKEND`、`DEEPSEEK_*`、`OPENAI_*`、`OLLAMA_*`
  - [x] Embedding 配置：`EMBEDDING_BACKEND`、`EMBEDDING_BGE_*`、`EMBEDDING_OPENAI_*`
  - [x] 向量数据库配置：`VECTOR_STORE_BACKEND`、`VECTOR_STORE_CHROMA_*`、`VECTOR_STORE_MILVUS_*`、`VECTOR_STORE_PGVECTOR_*`
  - [x] 检索配置：`RETRIEVAL_TOP_K`、`RETRIEVAL_MODE` 等
  - [x] 切片配置：`SPLITTER_TYPE`、`SPLITTER_CHUNK_SIZE`、`SPLITTER_CHUNK_OVERLAP`
  - [x] LLM 生成配置：`LLM_TEMPERATURE`、`LLM_MAX_TOKENS`
- [x] 添加字段验证器：`STORAGE_MAX_FILE_SIZE` 等范围校验
- [x] 创建全局单例 `settings = Settings()`

### 2. 默认配置文件

- [x] 创建 `backend/app/config/config.yaml`
- [x] 为所有配置项填入合理的默认值

### 3. .env 模板

- [x] 在 `backend/.env.example` 中添加配置管理对应的注释和示例

### 4. 测试

- [x] 创建 `backend/app/config/tests/__init__.py`
- [x] 创建 `backend/app/config/tests/test_settings.py`
  - [x] 测试默认值的正确性
  - [x] 测试环境变量覆盖默认值
  - [x] 测试 `STORAGE_MAX_FILE_SIZE` 等字段校验规则
- [x] 创建 `backend/app/config/tests/conftest.py`（设置测试用环境变量）

### 5. 验证

- [x] `Settings()` 加载无报错
- [x] 环境变量确能覆盖默认值
- [x] 字段校验器正常工作
- [x] `pytest backend/app/config/tests/` 全部通过（86 passed）

---

## 验收标准

- [x] 所有配置来自需求文档中的技术选型
- [x] 环境变量命名遵循 `{SECTION}_{KEY}` 规范（单下划线分隔前缀与键名）
- [x] 敏感字段（API Key）有明确标注（`Optional[str] = None` + `description`）
- [x] 测试覆盖默认值和校验规则（86 项测试）
