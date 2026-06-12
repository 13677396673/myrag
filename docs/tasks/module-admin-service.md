# M21：管理后台服务模块 (services/admin_service)

**阶段**: Phase 5 | **优先级**: P1 | **状态**: ✅ 已完成

**依赖模块**: M04 Database、M02 Models

**参考设计**: [详细设计文档 Module-21](../详细设计文档.md#module-21-管理后台服务模块-servicesadmin_service)

---

## 任务清单

### 1. AdminService

- [x] 创建 `backend/app/services/admin_service.py`
  - [x] `AdminService` 类
  - [x] `__init__(db: DatabaseManager)`
  - [x] `async list_users(page, page_size) -> dict`（分页）
    - [x] 包含 id、username、email、role、is_active、created_at
  - [x] `async get_stats() -> SystemStatsResponse`
    - [x] 统计：用户总数、文档总数、对话总数、切片总数、今日活跃用户
    - [x] 今日活跃 = updated_at = 今天的用户数

### 2. 测试

- [x] 创建 `backend/app/services/tests/test_admin_service.py`
  - [x] 使用内存 SQLite DatabaseManager
  - [x] 插入测试数据后验证统计值
  - [x] 测试用户列表分页
  - [x] 测试空数据库统计值（全 0）

### 3. 验证

- [x] `pytest backend/app/services/tests/test_admin_service.py` 全部通过

---

## 验收标准

- [x] 统计接口返回正确数值
- [x] 用户列表分页正确
