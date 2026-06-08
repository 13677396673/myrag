# M03：Pydantic 模式模块 (schemas)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: 无（完全独立）

**参考设计**: [详细设计文档 Module-03](../详细设计文档.md#module-03-pydantic-模式模块-schemas)

---

## 任务清单

### 1. 通用模式

- [x] 创建 `backend/app/schemas/__init__.py`
- [x] 创建 `backend/app/schemas/common.py`
  - [x] `ApiResponse[T]` — 统一响应包装
  - [x] `PaginatedResponse[T]` — 分页响应
  - [x] `PaginationParams` — 分页请求参数

### 2. 用户模式

- [x] 创建 `backend/app/schemas/user.py`
  - [x] `UserRegisterRequest`：username(2-50, 字母数字下划线)、email、password(6-128)
  - [x] `UserLoginRequest`：username、password
  - [x] `UserResponse`：id、username、email、role、is_active、created_at
  - [x] `UserUpdateRequest`：email(可选)
  - [x] `PasswordChangeRequest`：old_password、new_password(6-128)
  - [x] `TokenResponse`：access_token、token_type、user(UserResponse)

### 3. 数据集模式

- [x] 创建 `backend/app/schemas/dataset.py`
  - [x] `DatasetCreateRequest`：name(必填)、description(可选)
  - [x] `DatasetUpdateRequest`：name(可选)、description(可选)
  - [x] `DatasetResponse`：id、name、description、document_count、created_at、updated_at

### 4. 文档模式

- [x] 创建 `backend/app/schemas/document.py`
  - [x] `DocumentResponse`：id、filename、file_type、file_size、status、error_message、dataset_id、chunk_count、created_at、updated_at
  - [x] `DocumentStatusResponse`：id、status、progress(0~1)、error_message

### 5. 切片模式

- [x] 创建 `backend/app/schemas/chunk.py`
  - [x] `ChunkResponse`：id、document_id、content、chunk_index、metadata

### 6. 对话模式

- [x] 创建 `backend/app/schemas/conversation.py`
  - [x] `ConversationCreateRequest`：title(默认"新对话")、dataset_id(可选)
  - [x] `ConversationResponse`：id、title、dataset_id、message_count、created_at、updated_at
  - [x] `MessageSendRequest`：content(1-10000)
  - [x] `SourceCitation`：chunk_id、content、document_name、score
  - [x] `MessageResponse`：id、role、content、sources(list)、created_at
  - [x] `MessageStreamEvent`：type(delta/done/sources/error)、content

### 7. 管理后台模式

- [x] 创建 `backend/app/schemas/admin.py`
  - [x] `SystemStatsResponse`：total_users、total_documents、total_conversations、total_chunks、active_users_today

### 8. schemas/\_\_init\_\_.py

- [x] 导出所有模式类

### 9. 测试

- [x] 创建 `backend/app/schemas/tests/__init__.py`
- [x] 创建 `backend/app/schemas/tests/test_user_schemas.py`
  - [x] 测试用户注册请求校验（用户名过短/过长/非法字符、密码过短、邮箱格式）
  - [x] 测试用户响应序列化
- [x] 创建 `backend/app/schemas/tests/test_dataset_schemas.py`
  - [x] 测试数据集创建请求
- [x] 创建 `backend/app/schemas/tests/test_document_schemas.py`
  - [x] 测试文档响应格式
- [x] 创建 `backend/app/schemas/tests/test_conversation_schemas.py`
  - [x] 测试消息发送请求长度限制
  - [x] 测试 SSE 事件格式

### 10. 验证

- [x] 所有模式可导入无报错
- [x] `pydantic` 类型校验正常
- [x] `pytest backend/app/schemas/tests/` 全部通过（49 passed）

---

## 验收标准

- [ ] 每个 API 接口有对应的 Request/Response 模式
- [ ] 字段校验规则符合业务需求（用户名、密码、邮箱、文本长度等）
- [ ] `ApiResponse` 和 `PaginatedResponse` 泛型工作正常
- [ ] `MessageStreamEvent` 覆盖所有 SSE 事件类型
