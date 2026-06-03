# M04：数据库模块 (core/database)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M01 Config

**参考设计**: [详细设计文档 Module-04](../详细设计文档.md#module-04-数据库模块-coredatabase)

---

## 任务清单

### 1. DatabaseManager 类

- [ ] 创建 `backend/app/core/__init__.py`
- [ ] 创建 `backend/app/core/database.py`
  - [ ] 定义 `DatabaseManager` 类
  - [ ] `__init__(self, settings: Settings)` — 保存 settings 引用
  - [ ] `async initialize()` — 创建异步引擎和 session 工厂
    - [ ] SQLite 使用 `NullPool`
  - [ ] `async create_tables()` — 调用 `Base.metadata.create_all()`
  - [ ] `async close()` — 释放引擎
  - [ ] `get_session()` — 返回 `AsyncSession` 实例
  - [ ] `session_factory` 属性 — 返回 session 工厂

### 2. 全局异常

- [ ] 创建 `backend/app/core/exceptions.py`
  - [ ] `RagError` — 所有异常的基类（含 code、message、detail）
  - [ ] `ConfigError`
  - [ ] `StorageError`
  - [ ] 后续模块需要的异常基类

### 3. 测试

- [ ] 创建 `backend/app/core/tests/__init__.py`
- [ ] 创建 `backend/app/core/tests/test_database.py`
  - [ ] 测试用 SQLite 内存数据库初始化
  - [ ] 测试 `create_tables()` 创建了正确的表
  - [ ] 测试 `get_session()` 可以执行查询
  - [ ] 测试 `close()` 后数据库不可用
- [ ] 创建 `backend/app/core/tests/conftest.py`
  - [ ] Fixture：内存 SQLite 配置的 Settings
  - [ ] Fixture：初始化和清理后的 DatabaseManager

### 4. 验证

- [ ] `DatabaseManager` 能正常启动和关闭
- [ ] 表创建不报错
- [ ] pytest 全部通过

---

## 验收标准

- [ ] 支持 SQLite 和 PostgreSQL（通过 DATABASE_URL 切换）
- [ ] Session 使用 `async with` 上下文管理
- [ ] `close()` 被调用后释放所有资源
- [ ] 测试覆盖初始化和表创建
