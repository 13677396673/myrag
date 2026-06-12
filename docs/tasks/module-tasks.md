# M24：异步任务定义模块 (tasks)

**阶段**: Phase 7 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M15 Pipeline、M19 DocumentService

---

## 任务清单

### 1. 文档处理任务

- [x] 创建 `backend/app/tasks/__init__.py`
- [x] 创建 `backend/app/tasks/document_tasks.py`
  - [x] `process_document(doc_id: str)` — 文档处理主任务
    - [x] 1. 从 DB 获取 Document 记录（更新 status → "parsing"）
    - [x] 2. 调用 pipeline.process_document(file_path, doc_id, user_id, dataset_id)
    - [x] 3. 更新 DB（status → "completed", chunk_count, vector_id 等）
    - [x] 4. 错误处理（捕获异常 → status → "failed" + 记录 error_message）
  - [x] 注册任务到 TaskQueue（在 tasks/\_\_init\_\_.py 中 export 注册函数）

### 2. 测试

- [x] 创建 `backend/app/tasks/tests/__init__.py`
- [x] 创建 `backend/app/tasks/tests/test_document_tasks.py`
  - [x] Mock DatabaseManager
  - [x] Mock DocumentPipeline
  - [x] 测试处理成功流程：status 从 pending → parsing → completed
  - [x] 测试处理失败流程：status → failed, error_message 被记录
  - [x] 测试文档不存在时的处理

### 3. 验证

- [x] 任务可被 TaskQueue 调度
- [x] `pytest backend/app/tasks/tests/` 全部通过

---

## 验收标准

- [x] 文档异步处理完整流程
- [x] 状态更新正确
- [x] 错误时状态置为 failed 并记录原因
