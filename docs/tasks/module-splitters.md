# M10：文本切片器模块 (rag/splitters)

**阶段**: Phase 3 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M08 Interfaces

**参考设计**: [详细设计文档 Module-10](../详细设计文档.md#module-10-文本切片器模块-ragsplitters)

---

## 任务清单

### 1. FixedSizeSplitter

- [x] 创建 `backend/app/rag/splitters/__init__.py`
- [x] 创建 `backend/app/rag/splitters/fixed_splitter.py`
  - [x] `FixedSizeSplitter(TextSplitter)`
  - [x] `__init__(chunk_size=512, chunk_overlap=64)`
  - [x] 校验 `chunk_overlap < chunk_size`，否则抛 ValueError
  - [x] `split(text, metadata) -> List[DocumentChunk]`
  - [x] 按字符数切分（非 token 数，MVP 阶段用字符数简化）
  - [x] overlap 逻辑正确
  - [x] `type_name` 返回 `"fixed"`

### 2. 预留切片器

- [x] 创建 `backend/app/rag/splitters/markdown_splitter.py`（占位）
- [x] 创建 `backend/app/rag/splitters/semantic_splitter.py`（占位）

### 3. 测试

- [x] 创建 `backend/app/rag/splitters/tests/__init__.py`
- [x] 创建 `backend/app/rag/splitters/tests/test_fixed_splitter.py`
  - [x] 测试短文本（< chunk_size）→ 返回 1 个 chunk
  - [x] 测试长文本 → 返回多个 chunk
  - [x] 测试 overlap 逻辑正确
  - [x] 测试 overlap >= chunk_size → 抛 ValueError
  - [x] 测试空文本 → 返回空列表
  - [x] 测试 metadata 传递到每个 chunk
  - [x] 测试 chunk_index 正确递增

### 4. 验证

- [x] 切片逻辑严谨（边界情况覆盖）
- [x] `pytest backend/app/rag/splitters/tests/` 全部通过

---

## 验收标准

- [x] 切片大小和 overlap 可配置
- [x] overlap 校验严格
- [x] metadata 正确透传到每个 chunk
- [x] chunk_index 从 0 开始递增
