# M06：文件存储模块 (core/storage)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M01 Config

**参考设计**: [详细设计文档 Module-06](../详细设计文档.md#module-06-文件存储模块-corestorage)

---

## 任务清单

### 1. 抽象接口

- [x] 创建 `backend/app/core/storage/__init__.py`
- [x] 创建 `backend/app/core/storage/base.py`
  - [x] `FileStorageBackend` 抽象类
  - [x] `async save(file_path: str, content: bytes) -> str`
  - [x] `async read(storage_path: str) -> Optional[bytes]`
  - [x] `async delete(storage_path: str) -> bool`
  - [x] `async exists(storage_path: str) -> bool`

### 2. 本地文件存储实现

- [x] 创建 `backend/app/core/storage/local_storage.py`
  - [x] `LocalFileStorage(FileStorageBackend)`
  - [x] `__init__(base_path: str)` — 确保目录存在
  - [x] `save()` — 写入文件（自动创建中间目录）
  - [x] `read()` — 返回 bytes 或 None
  - [x] `delete()` — 删除文件
  - [x] `exists()` — 检查文件存在

### 3. 测试

- [x] 创建 `backend/app/core/tests/test_local_storage.py`
  - [x] 测试保存文件 → 读取内容一致
  - [x] 测试读取不存在的文件 → 返回 None
  - [x] 测试删除存在的文件 → 返回 True
  - [x] 测试删除不存在的文件 → 返回 False
  - [x] 测试保存到嵌套子目录 → 自动创建中间目录
  - [x] 测试覆盖二进制内容保存（如 PDF、图片）
- [x] 创建 `backend/app/core/tests/conftest.py`（更新）
  - [x] Fixture：`tmp_dir` 使用 `tempfile.TemporaryDirectory`
  - [x] Fixture：`local_storage` 注入 tmp_dir

### 4. 验证

- [x] 文件读写生命周期完整
- [x] 大文件（接近 max_file_size）读写正常
- [x] `pytest backend/app/core/tests/test_local_storage.py` 全部通过

---

## 验收标准

- [ ] 接口清晰，支持替换为 S3/MinIO 实现
- [ ] 路径自动创建中间目录
- [ ] 所有方法为 async
- [ ] 文件不存在时 read 返回 None（不抛异常）
