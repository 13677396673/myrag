# M20：对话服务模块 (services/conversation_service)

**阶段**: Phase 5 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M04 Database、M16 RAG Engine

**参考设计**: [详细设计文档 Module-20](../详细设计文档.md#module-20-对话服务模块-servicesconversation_service)

---

## 任务清单

### 1. ConversationService

- [ ] 创建 `backend/app/services/conversation_service.py`
  - [ ] `ConversationService` 类
  - [ ] `__init__(db, rag_engine)`
  - [ ] `async create_conversation(request, user_id) -> ConversationResponse`
  - [ ] `async list_conversations(user_id, page, page_size) -> dict`
  - [ ] `async get_conversation(conv_id, user_id) -> ConversationResponse`
  - [ ] `async delete_conversation(conv_id, user_id)`
  - [ ] `async get_messages(conv_id, user_id, page, page_size) -> dict`
  - [ ] `async send_message(conv_id, request, user_id) -> AsyncIterator[dict]`
    - [ ] 保存用户消息到 DB
    - [ ] 获取历史消息
    - [ ] 构建 filter_conditions（user_id + 可选的 dataset_id）
    - [ ] 调用 rag_engine.query_stream()
    - [ ] 收集完整回答
    - [ ] 保存 assistant 消息到 DB
    - [ ] 保存消息-切片关联（MessageChunk）
    - [ ] 如果是第一条回复，自动更新对话标题（取用户消息前 50 字）
    - [ ] yield 所有事件
  - [ ] `_get_history(conv_id) -> List[dict]`（内部方法）
  - [ ] `_to_msg_response(msg) -> dict`（内部方法）
  - [ ] `_to_conv_response(conv) -> ConversationResponse`（内部方法）

### 2. 测试

- [ ] 创建 `backend/app/services/tests/test_conversation_service.py`
  - [ ] Mock `RAGEngine`
  - [ ] 使用内存 SQLite DatabaseManager
  - [ ] 测试创建对话
  - [ ] 测试列出对话
  - [ ] 测试获取对话详情
  - [ ] 测试删除对话（级联删除消息）
  - [ ] 测试发送消息
    - [ ] 验证 RAGEngine.query_stream 被调用
    - [ ] 验证用户消息被保存
    - [ ] 验证 assistant 消息被保存
    - [ ] 验证来源引用被保存
  - [ ] 测试第一条回复自动更新标题
  - [ ] 测试对话不存在的处理
  - [ ] 测试获取消息列表

### 3. 验证

- [ ] `pytest backend/app/services/tests/test_conversation_service.py` 全部通过

---

## 验收标准

- [ ] 对话的 CRUD 完整
- [ ] 发送消息 → RAGEngine 调用 → 保存完整对话历史
- [ ] 流式 yield 事件格式正确
- [ ] 首条自动标题功能
- [ ] 来源引用持久化
