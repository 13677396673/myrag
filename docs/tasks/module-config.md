# M01：配置管理模块 (config)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: 无（完全独立）

**参考设计**: [详细设计文档 Module-01](../详细设计文档.md#module-01-配置管理模块-config)

---

## 任务清单

### 1. Settings 类

- [ ] 创建 `backend/app/config/__init__.py`
- [ ] 创建 `backend/app/config/settings.py`
  - [ ] 定义 `Settings` 类（继承 `pydantic-settings.BaseSettings`）
  - [ ] 应用基础配置：`APP_NAME`、`APP_VERSION`、`APP_DEBUG`
  - [ ] 服务配置：`SERVER_HOST`、`SERVER_PORT`、`SERVER_CORS_ORIGINS`
  - [ ] 数据库配置：`DATABASE_URL`、`DATABASE_ECHO`
  - [ ] JWT 配置：`JWT_SECRET_KEY`、`JWT_ALGORITHM`、`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
  - [ ] 文件存储配置：`STORAGE_BACKEND`、`STORAGE_LOCAL_PATH`、`STORAGE_MAX_FILE_SIZE`、`STORAGE_S3_*`
  - [ ] 任务队列配置：`TASK_QUEUE_BACKEND`、`TASK_QUEUE_REDIS_URL`
  - [ ] LLM 配置：`LLM_BACKEND`、`DEEPSEEK_*`、`OPENAI_*`、`OLLAMA_*`
  - [ ] Embedding 配置：`EMBEDDING_BACKEND`、`EMBEDDING_BGE_*`、`EMBEDDING_OPENAI_*`
  - [ ] 向量数据库配置：`VECTOR_STORE_BACKEND`、`VECTOR_STORE_CHROMA_*`、`VECTOR_STORE_MILVUS_*`、`VECTOR_STORE_PGVECTOR_*`
  - [ ] 检索配置：`RETRIEVAL_TOP_K`、`RETRIEVAL_MODE` 等
  - [ ] 切片配置：`SPLITTER_TYPE`、`SPLITTER_CHUNK_SIZE`、`SPLITTER_CHUNK_OVERLAP`
  - [ ] LLM 生成配置：`LLM_TEMPERATURE`、`LLM_MAX_TOKENS`
- [ ] 添加字段验证器：`STORAGE_MAX_FILE_SIZE` 范围校验
- [ ] 创建全局单例 `settings = Settings()`

### 2. 默认配置文件

- [ ] 创建 `backend/app/config/config.yaml`
- [ ] 为所有配置项填入合理的默认值

### 3. .env 模板

- [ ] 在 `backend/.env.example` 中添加配置管理对应的注释和示例

### 4. 测试

- [ ] 创建 `backend/app/config/tests/__init__.py`
- [ ] 创建 `backend/app/config/tests/test_settings.py`
  - [ ] 测试默认值的正确性
  - [ ] 测试环境变量覆盖默认值
  - [ ] 测试 `STORAGE_MAX_FILE_SIZE` 校验规则
- [ ] 创建 `backend/app/config/tests/conftest.py`（设置测试用环境变量）

### 5. 验证

- [ ] `Settings()` 加载无报错
- [ ] 环境变量确能覆盖默认值
- [ ] 字段校验器正常工作
- [ ] `pytest backend/app/config/tests/` 全部通过

---

## 验收标准

- [ ] 所有配置来自需求文档中的技术选型
- [ ] 环境变量命名遵循 `{SECTION}__{KEY}` 规范
- [ ] 敏感字段（API Key）有明确标注
- [ ] 测试覆盖默认值和校验规则
