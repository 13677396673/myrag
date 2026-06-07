# M02：ORM 模型模块 (models)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: 无（完全独立）

**参考设计**: [详细设计文档 Module-02](../详细设计文档.md#module-02-orm-模型模块-models)

---

## 任务清单

### 1. 基类与工具

- [x] 创建 `backend/app/models/__init__.py`
- [x] 创建 `backend/app/models/base.py`
  - [x] 定义 `Base`（`DeclarativeBase`）
  - [x] 定义 `generate_uuid()` 函数
  - [x] 定义 `TimestampMixin`（`created_at`、`updated_at`）
- [x] 创建 `backend/app/models/mixins.py`（可选，已将 TimestampMixin 放 base.py）

### 2. 用户模型

- [x] 创建 `backend/app/models/user.py`
  - [x] `User` 类，表名 `users`
  - [x] 字段：`id`(PK)、`username`(UNIQUE)、`email`(UNIQUE)、`password_hash`、`role`、`is_active`
  - [x] 引入 `TimestampMixin`

### 3. 数据集模型

- [x] 创建 `backend/app/models/dataset.py`
  - [x] `Dataset` 类，表名 `datasets`
  - [x] 字段：`id`(PK)、`name`、`description`、`user_id`(FK)
  - [x] 关系：`owner` → User、`documents` → Document（`cascade="all, delete-orphan"`）

### 4. 文档模型

- [x] 创建 `backend/app/models/document.py`
  - [x] `Document` 类，表名 `documents`
  - [x] 字段：`id`(PK)、`filename`、`file_type`、`file_size`、`file_path`、`status`、`error_message`、`dataset_id`(FK)、`user_id`(FK)、`chunk_count`
  - [x] 关系：`chunks` → Chunk（`cascade="all, delete-orphan"`）

### 5. 切片模型

- [x] 创建 `backend/app/models/chunk.py`
  - [x] `Chunk` 类，表名 `chunks`
  - [x] 字段：`id`(PK)、`document_id`(FK)、`content`、`chunk_index`、`meta_data`(JSON 列 "metadata")、`vector_id`
  - [x] 关系：`message_links` → MessageChunk

### 6. 对话与消息模型

- [x] 创建 `backend/app/models/conversation.py`
  - [x] `Conversation` 类，表名 `conversations`
  - [x] 字段：`id`(PK)、`title`、`user_id`(FK)、`dataset_id`(FK)
  - [x] 关系：`messages` → Message（`cascade="all, delete-orphan"`）
- [x] 创建 `backend/app/models/message.py`
  - [x] `Message` 类，表名 `messages`
  - [x] 字段：`id`(PK)、`conversation_id`(FK)、`role`、`content`、`meta_data`(JSON 列 "metadata")
  - [x] 关系：`source_chunks` → MessageChunk
  - [x] `MessageChunk` 关联表，字段：`id`(PK)、`message_id`(FK)、`chunk_id`(FK)、`relevance_score`

### 7. models/\_\_init\_\_.py

- [x] 导出所有模型类
- [x] 确保 `__all__` 完整

### 8. 测试

- [x] 创建 `backend/app/models/tests/__init__.py`
- [x] 创建 `backend/app/models/tests/conftest.py`
  - [x] 创建 SQLite 内存引擎
  - [x] 创建所有表
- [x] 创建 `backend/app/models/tests/test_user.py`
  - [x] 测试创建用户
  - [x] 测试用户名唯一约束
  - [x] 测试邮箱唯一约束
- [x] 创建 `backend/app/models/tests/test_dataset.py`
  - [x] 测试创建数据集
  - [x] 测试用户与数据集的关系
- [x] 创建 `backend/app/models/tests/test_document.py`
  - [x] 测试创建文档
  - [x] 测试文档状态默认值
  - [x] 测试文档与数据集的关系
- [x] 创建 `backend/app/models/tests/test_conversation.py`
  - [x] 测试创建对话与消息
  - [x] 测试级联删除

### 9. 验证

- [x] 所有模型可通过 `Base.metadata.create_all()` 建表
- [x] 测试插入与查询数据
- [x] 验证外键约束和级联删除
- [x] `pytest backend/app/models/tests/` 全部通过

---

## 验收标准

- [ ] 7 张表的字段定义与详细设计完全一致
- [ ] 所有外键和关系定义正确
- [ ] JSON 字段类型兼容 SQLite 和 PostgreSQL
- [ ] 级联删除链路完整（Dataset → Document → Chunk → MessageChunk）
