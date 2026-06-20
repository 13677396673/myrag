# M10：文本切片器模块 (rag/splitters)

**阶段**: Phase 3 | **优先级**: P0 | **状态**: ✅ 已完成（v2 新增 MarkdownSplitter + PDFPageSplitter）

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
  - [x] `split(text, metadata, sections=None) -> List[DocumentChunk]`
  - [x] 按字符数切分（非 token 数，MVP 阶段用字符数简化）
  - [x] overlap 逻辑正确
  - [x] `type_name` 返回 `"fixed"`

### 2. MarkdownSplitter

- [x] 创建 `backend/app/rag/splitters/markdown_splitter.py`
  - [x] `MarkdownSplitter(TextSplitter)`
  - [x] `__init__(chunk_size=512, chunk_overlap=0)`
  - [x] `split(text, metadata, sections) -> List[DocumentChunk]`
  - [x] 按 Markdown 标题（`#` ~ `######`）边界切分
  - [x] 标题层级链（h1~h6）写入每个 chunk 的 metadata
  - [x] 超长 section 按段落子切分，标题链保留
  - [x] sections 参数优先；无 sections 时自行从 text 解析标题
  - [x] `type_name` 返回 `"markdown"`

### 3. PDFPageSplitter

- [x] 创建 `backend/app/rag/splitters/pdf_page_splitter.py`
  - [x] `PDFPageSplitter(TextSplitter)`
  - [x] `__init__(chunk_size=512, chunk_overlap=0)`
  - [x] `split(text, metadata, sections) -> List[DocumentChunk]`
  - [x] 按 sections 中的 page 边界切分
  - [x] `page_number` 写入每个 chunk 的 metadata
  - [x] 超长页内容按段落子切分，page_number 一致
  - [x] 无 sections / 无 page 字段时回退为固定大小切分
  - [x] `type_name` 返回 `"pdf_page"`

### 4. 预留切片器

- [x] 创建 `backend/app/rag/splitters/semantic_splitter.py`（占位）

### 5. 测试

#### FixedSizeSplitter
- [x] 创建 `backend/app/rag/splitters/tests/__init__.py`
- [x] 创建 `backend/app/rag/splitters/tests/test_fixed_splitter.py`
  - [x] 测试短文本（< chunk_size）→ 返回 1 个 chunk
  - [x] 测试长文本 → 返回多个 chunk
  - [x] 测试 overlap 逻辑正确
  - [x] 测试 overlap >= chunk_size → 抛 ValueError
  - [x] 测试空文本 → 返回空列表
  - [x] 测试 metadata 传递到每个 chunk
  - [x] 测试 chunk_index 正确递增

#### MarkdownSplitter
- [x] 创建 `backend/app/rag/splitters/tests/test_markdown_splitter.py`
  - [x] 测试按标题边界切分
  - [x] 测试标题层级链正确传递
  - [x] 测试 sections 方式 vs 自解析方式
  - [x] 测试长 section 子切分
  - [x] 测试无标题文档回退行为

#### PDFPageSplitter
- [x] 创建 `backend/app/rag/splitters/tests/test_pdf_page_splitter.py`
  - [x] 测试按 page 边界切分
  - [x] 测试 page_number 写入 metadata
  - [x] 测试长页子切分后 page_number 一致
  - [x] 测试无 sections 时回退行为

### 6. 验证

- [x] 所有切片器逻辑严谨（边界情况覆盖）
- [x] `pytest backend/app/rag/splitters/tests/` 全部通过

---

## 验收标准

- [x] 切片大小和 overlap 可配置
- [x] overlap 校验严格
- [x] metadata 正确透传到每个 chunk
- [x] chunk_index 从 0 开始递增
- [x] sections 参数向下兼容（不传则行为不变）
- [x] Markdown 标题感知切分完整
- [x] PDF 页码感知切分完整
