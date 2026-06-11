# M18：数据集服务模块 (services/dataset_service)

**阶段**: Phase 5 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M01 Config, M04 Database, M02 Models (Dataset), M03 Schemas (Dataset)

**参考设计**: [详细设计文档 Module-18](../详细设计文档.md#module-18-数据集服务模块-servicesdataset_service)

---

## 任务清单

### 1. 服务异常定义

- [x] 在 `backend/app/services/dataset_service.py` 中定义业务异常类
  - [x] `DatasetServiceError` — 数据集服务异常基类（继承 `RagError`）
  - [x] `DatasetNotFound` — 数据集不存在（含 dataset_id）
  - [x] `DatasetPermissionDenied` — 无权访问该数据集

### 2. DatasetService 类

- [x] 创建 `backend/app/services/dataset_service.py`
  - [x] 定义 `DatasetService` 类
  - [x] `__init__(self, db: DatabaseManager)` — 仅依赖数据库
  - [x] `create(request: DatasetCreateRequest, user_id: str) -> DatasetResponse`
    - [x] 创建并返回文档计数为 0 的响应
  - [x] `get_dataset(dataset_id: str, user_id: str) -> DatasetResponse`
    - [x] 不存在 → DatasetNotFound
    - [x] 非本人数据集 → DatasetPermissionDenied
    - [x] 返回正确的 document_count
  - [x] `list_datasets(user_id: str, page, page_size) -> Tuple[list, int]`
    - [x] 只返回本人的数据集（user_id 过滤）
    - [x] 按创建时间倒序排列
    - [x] 支持分页
    - [x] 批量查询文档计数（避免 N+1）
  - [x] `update_dataset(dataset_id, request, user_id) -> DatasetResponse`
    - [x] 支持部分更新（name/description 可选）
  - [x] `delete_dataset(dataset_id, user_id) -> None`
    - [x] 级联删除关联文档（ORM cascade）
  - [x] `_to_response(dataset, document_count) -> DatasetResponse` — 静态转换
  - [x] `_count_documents(session, dataset_id) -> int` — 单个文档计数
  - [x] `_batch_count_documents(session, dataset_ids) -> dict` — 批量文档计数
- [x] 更新 `backend/app/services/__init__.py` — 导出 DatasetService 及异常类

### 3. 测试

- [x] 更新 `backend/app/services/tests/conftest.py`
  - [x] `dataset_service` fixture — DatasetService 实例
  - [x] `another_user` fixture — 额外测试用户（用于用户隔离测试）
  - [x] `sample_dataset` fixture — 预创建的测试数据集
- [x] 创建 `backend/app/services/tests/test_dataset_service.py`（24 项测试）
  - [x] **创建测试（2 项）** — 成功、无描述
  - [x] **获取测试（3 项）** — 本人、他人、不存在
  - [x] **列表测试（5 项）** — 空列表、有数据、用户隔离、分页、顺序
  - [x] **更新测试（4 项）** — 全更新、部分更新、他人、不存在
  - [x] **删除测试（3 项）** — 本人、他人、不存在
  - [x] **级联删除测试（1 项）** — 删除数据集后文档也被删除
  - [x] **文档计数测试（3 项）** — 创建时为 0、获取时正确、列表中正确
  - [x] **异常错误码验证（3 项）** — 所有异常类的 code/message 正确

### 4. 验证

- [x] `from app.services import DatasetService` 无报错
- [x] `DatasetService` 构造函数接受 `DatabaseManager`
- [x] 所有公开方法正确使用 async session
- [x] 用户隔离严格（无法访问他人的数据集）
- [x] 删除数据集级联删除文档
- [x] 文档计数批量查询（列表场景无 N+1）
- [x] `pytest backend/app/services/tests/` 全部通过（54 passed：24 dataset + 30 user）

---

## 验收标准

- [x] 数据集的 CRUD 完整
- [x] 用户隔离严格（用户 A 不能操作用户 B 的数据集）
- [x] 删除数据集级联删除文档（通过 ORM cascade 实现）
- [x] 分页接口返回 total 和分页数据
- [x] document_count 真实反映文档数量（批量查询无 N+1）
- [x] 测试覆盖正常流程和所有异常分支（24 项测试）
