# M02：ORM 模型模块 (models)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: 无（完全独立）

**参考设计**: [详细设计文档 Module-02](../详细设计文档.md#module-02-orm-模型模块-models)

---

## 任务清单

### 1. 基类与工具

- [ ] 创建 `backend/app/models/__init__.py`
- [ ] 创建 `backend/app/models/base.py`
  - [ ] 定义 `Base`（`DeclarativeBase`）
  - [ ] 定义 `generate_uuid()` 函数
  - [ ] 定义 `TimestampMixin`（`created_at`、`updated_at`）
- [ ] 创建 `backend/app/models/mixins.py`（可选，可将 TimestampMixin 放此）

### 2. 用户模型

- [ ] 创建 `backend/app/models/user.py`
  - [ ] `User` 类，表名 `users`
  - [ ] 字段：`id`(PK)、`username`(UNIQUE)、`email`(UNIQUE)、`password_hash`、`role`、`is_active`
  - [ ] 引入 `TimestampMixin`

### 3. 数据集模型

- [ ] 创建 `backend/app/models/dataset.py`
  - [ ] `Dataset` 类，表名 `datasets`
  - [ ] 字段：`id`(PK)、`name`、`description`、`user_id`(FK)
  - [ ] 关系：`owner` → User、`documents` → Document（`cascade="all, delete-orphan"`）

### 4. 文档模型

- [ ] 创建 `backend/app/models/document.py`
  - [ ] `Document` 类，表名 `documents`
  - [ ] 字段：`id`(PK)、`filename`、`file_type`、`file_size`、`file_path`、`status`、`error_message`、`dataset_id`(FK)、`user_id`(FK)、`chunk_count`
  - [ ] 关系：`chunks` → Chunk（`cascade="all, delete-orphan"`）

### 5. 切片模型

- [ ] 创建 `backend/app/models/chunk.py`
  - [ ] `Chunk` 类，表名 `chunks`
  - [ ] 字段：`id`(PK)、`document_id`(FK)、`content`、`chunk_index`、`metadata`(JSON)、`vector_id`
  - [ ] 关系：`message_links` → MessageChunk

### 6. 对话与消息模型

- [ ] 创建 `backend/app/models/conversation.py`
  - [ ] `Conversation` 类，表名 `conversations`
  - [ ] 字段：`id`(PK)、`title`、`user_id`(FK)、`dataset_id`(FK)
  - [ ] 关系：`messages` → Message（`cascade="all, delete-orphan"`）
- [ ] 创建 `backend/app/models/message.py`
  - [ ] `Message` 类，表名 `messages`
  - [ ] 字段：`id`(PK)、`conversation_id`(FK)、`role`、`content`、`metadata`(JSON)
  - [ ] 关系：`source_chunks` → MessageChunk
  - [ ] `MessageChunk` 关联表，字段：`id`(PK)、`message_id`(FK)、`chunk_id`(FK)、`relevance_score`

### 7. models/\_\_init\_\_.py

- [ ] 导出所有模型类
- [ ] 确保 `__all__` 完整

### 8. 测试

- [ ] 创建 `backend/app/models/tests/__init__.py`
- [ ] 创建 `backend/app/models/tests/conftest.py`
  - [ ] 创建 SQLite 内存引擎
  - [ ] 创建所有表
- [ ] 创建 `backend/app/models/tests/test_user.py`
  - [ ] 测试创建用户
  - [ ] 测试用户名唯一约束
  - [ ] 测试邮箱唯一约束
- [ ] 创建 `backend/app/models/tests/test_dataset.py`
  - [ ] 测试创建数据集
  - [ ] 测试用户与数据集的关系
- [ ] 创建 `backend/app/models/tests/test_document.py`
  - [ ] 测试创建文档
  - [ ] 测试文档状态默认值
  - [ ] 测试文档与数据集的关系
- [ ] 创建 `backend/app/models/tests/test_conversation.py`
  - [ ] 测试创建对话与消息
  - [ ] 测试级联删除

### 9. 验证

- [ ] 所有模型可通过 `Base.metadata.create_all()` 建表
- [ ] 测试插入与查询数据
- [ ] 验证外键约束和级联删除
- [ ] `pytest backend/app/models/tests/` 全部通过

---

## 验收标准

- [ ] 7 张表的字段定义与详细设计完全一致
- [ ] 所有外键和关系定义正确
- [ ] JSON 字段类型兼容 SQLite 和 PostgreSQL
- [ ] 级联删除链路完整（Dataset → Document → Chunk → MessageChunk）
