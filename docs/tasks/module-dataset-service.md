# M18：数据集服务模块 (services/dataset_service)

**阶段**: Phase 5 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M04 Database、M02 Models、M03 Schemas

**参考设计**: [详细设计文档 Module-18](../详细设计文档.md#module-18-数据集服务模块-servicesdataset_service)

---

## 任务清单

### 1. DatasetService

- [ ] 创建 `backend/app/services/dataset_service.py`
  - [ ] `DatasetService` 类
  - [ ] `__init__(db: DatabaseManager)`
  - [ ] `async create(request, user_id) -> DatasetResponse`
  - [ ] `async list_datasets(user_id, page, page_size) -> dict`（分页）
  - [ ] `async get_dataset(dataset_id, user_id) -> DatasetResponse`
    - [ ] 只允许访问自己的数据集
    - [ ] 不存在 → ValueError
  - [ ] `async update_dataset(dataset_id, request, user_id) -> DatasetResponse`
  - [ ] `async delete_dataset(dataset_id, user_id)`
    - [ ] 级联删除内部文档
  - [ ] `_to_response(dataset) -> DatasetResponse`
    - [ ] 包含 document_count（通过关系 count）

### 2. 测试

- [ ] 创建 `backend/app/services/tests/test_dataset_service.py`
  - [ ] 创建数据集成功
  - [ ] 列出数据集分页正确
  - [ ] 获取自己的数据集成功
  - [ ] 获取别人的数据集 → ValueError（用户隔离）
  - [ ] 更新数据集
  - [ ] 删除自己的数据集成功
  - [ ] 删除别人的数据集 → ValueError
  - [ ] 删除数据集后文档也被级联删除

### 3. 验证

- [ ] `pytest backend/app/services/tests/test_dataset_service.py` 全部通过

---

## 验收标准

- [ ] 数据集的 CRUD 完整
- [ ] 用户隔离严格（用户 A 不能操作用户 B 的数据集）
- [ ] 删除数据集级联删除文档
- [ ] 分页接口返回 total
