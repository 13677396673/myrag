# M19：文档服务模块 (services/document_service)

**阶段**: Phase 5 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M04 Database、M06 Storage、M07 TaskQueue、M15 Pipeline

**参考设计**: [详细设计文档 Module-19](../详细设计文档.md#module-19-文档服务模块-servicesdocument_service)

---

## 任务清单

### 1. DocumentService

- [ ] 创建 `backend/app/services/document_service.py`
  - [ ] `DocumentService` 类
  - [ ] `__init__(db, storage, task_queue, pipeline)`
  - [ ] `ALLOWED_EXTENSIONS` 常量（txt/md/pdf/docx/pptx/xlsx/png/jpg）
  - [ ] `async upload_document(user_id, dataset_id, filename, content) -> DocumentResponse`
    - [ ] 检查文件扩展名
    - [ ] 调用 storage.save()
    - [ ] 创建 Document 记录（status="pending"）
    - [ ] 入队异步处理任务 `task_queue.enqueue("process_document", doc_id)`
  - [ ] `async get_document(doc_id, user_id) -> DocumentResponse`
  - [ ] `async list_documents(dataset_id, user_id, page, page_size) -> dict`
  - [ ] `async delete_document(doc_id, user_id)`
    - [ ] 删除文件（storage.delete）
    - [ ] 删除数据库记录
  - [ ] `async get_document_status(doc_id, user_id) -> DocumentStatusResponse`
    - [ ] status → progress 映射
  - [ ] `async list_chunks(doc_id, user_id, page, page_size) -> dict`
  - [ ] `_to_response(doc) -> DocumentResponse`

### 2. 测试

- [ ] 创建 `backend/app/services/tests/test_document_service.py`
  - [ ] Mock `FileStorageBackend`
  - [ ] Mock `TaskQueueBackend`
  - [ ] Mock `DocumentPipeline`
  - [ ] 使用内存 SQLite DatabaseManager
  - [ ] 测试上传文档成功
    - [ ] 验证 storage.save 被调用
    - [ ] 验证 task_queue.enqueue 被调用
  - [ ] 测试不支持的格式 → ValueError
  - [ ] 测试获取文档列表
  - [ ] 测试获取不存在的文档 → ValueError
  - [ ] 测试删除文档（验证 storage.delete 和 DB 删除）
  - [ ] 测试文档状态查询
  - [ ] 测试查询切片列表

### 3. 验证

- [ ] `pytest backend/app/services/tests/test_document_service.py` 全部通过

---

## 验收标准

- [ ] 文档上传 → file storage → DB 记录 → 异步触发 流程完整
- [ ] 文件类型白名单校验
- [ ] 状态映射正确（pending→0, parsing→0.2, splitting→0.4, indexing→0.7, completed→1.0）
- [ ] 用户隔离（只能查删自己的文档）
