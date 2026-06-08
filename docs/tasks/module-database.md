# M04：数据库模块 (core/database)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M01 Config

**参考设计**: [详细设计文档 Module-04](../详细设计文档.md#module-04-数据库模块-coredatabase)

---

## 任务清单

### 1. DatabaseManager 类

- [x] 创建 `backend/app/core/__init__.py`
- [x] 创建 `backend/app/core/database.py`
  - [x] 定义 `DatabaseManager` 类
  - [x] `__init__(self, settings: Settings)` — 保存 settings 引用
  - [x] `async initialize()` — 创建异步引擎和 session 工厂
    - [x] SQLite 使用 `NullPool`
  - [x] `async create_tables()` — 调用 `Base.metadata.create_all()`
  - [x] `async close()` — 释放引擎
  - [x] `get_session()` — 返回 `AsyncSession` 实例
  - [x] `session_factory` 属性 — 返回 session 工厂

### 2. 全局异常

- [x] 创建 `backend/app/core/exceptions.py`
  - [x] `RagError` — 所有异常的基类（含 code、message、detail）
  - [x] `ConfigError`
  - [x] `StorageError`
  - [x] 后续模块需要的异常基类（`DatabaseError`）

### 3. 测试

- [x] 创建 `backend/app/core/tests/__init__.py`
- [x] 创建 `backend/app/core/tests/test_database.py`
  - [x] 测试用 SQLite 内存数据库初始化（改用临时文件避免 NullPool 隔离问题）
  - [x] 测试 `create_tables()` 创建了正确的表
  - [x] 测试 `get_session()` 可以执行查询
  - [x] 测试 `close()` 后数据库不可用
- [x] 创建 `backend/app/core/tests/conftest.py`
  - [x] Fixture：临时文件 SQLite 配置的 Settings
  - [x] Fixture：初始化和清理后的 DatabaseManager

### 4. 验证

- [x] `DatabaseManager` 能正常启动和关闭
- [x] 表创建不报错
- [x] pytest 全部通过

---

## 验收标准

- [x] 支持 SQLite 和 PostgreSQL（通过 DATABASE_URL 切换）
- [x] Session 使用 `async with` 上下文管理
- [x] `close()` 被调用后释放所有资源
- [x] 测试覆盖初始化和表创建

## 实现说明

- SQLite 使用 `NullPool` 避免多协程文件锁定
- **测试注意**：SQLite 内存数据库 (`sqlite+aiosqlite://`) + `NullPool` 会导致每个连接拥有独立的内存库，`create_tables()` 创建的表在 `get_session()` 的新连接中不可见。因此测试使用临时文件数据库 (`tempfile.mkstemp`) 而非内存库。
