# M15：文档处理管道模块 (rag/pipeline)

**阶段**: Phase 4 | **优先级**: P0 | **状态**: ✅ 已完成（v2 策略路由重构）

**依赖模块**: M08 Interfaces、M09 Parsers、M10 Splitters、M11 Embedding、M12 VectorStore、**M26 Strategies**

**参考设计**: [详细设计文档 Module-15](../详细设计文档.md#module-15-文档处理管道模块-ragpipeline)

---

## 任务清单

### 1. DocumentPipeline

- [x] 创建 `backend/app/rag/pipeline.py`
  - [x] `DocumentPipeline` 类
  - [x] ~~`__init__(parser_router, splitter, embedding, vector_store)`~~ （v2 已废弃）
  - [x] **`__init__(strategy_router, embedding, vector_store)`**（v2 改用策略路由）
  - [x] `process_document(file_path, document_id, user_id, dataset_id) -> int`
    - [x] Step 1: 根据文件扩展名从 **StrategyRouter** 获取策略
    - [x] Step 2: 调用 **strategy.execute()**（内部调用 parser.parse + splitter.split）
    - [x] Step 3: 调用 embedding.embed_documents(texts)
    - [x] Step 4: 调用 vector_store.add_embeddings(ids, vectors, metadatas)
    - [x] Step 5: 返回 chunk 数量
  - [x] chunk ID 格式：`{document_id}_{chunk_index}`
  - [x] sections 从 parser 透传到 splitter

### 2. 测试

- [x] 创建 `backend/app/rag/tests/__init__.py`
- [x] 创建 `backend/app/rag/tests/test_pipeline.py`
  - [x] Mock `StrategyRouter`
  - [x] Mock `ChunkingStrategy`
  - [x] Mock `TextSplitter`
  - [x] Mock `EmbeddingBackend`
  - [x] Mock `VectorStore`
  - [x] 测试完整流程：解析 → 切片 → Embedding → 存储
  - [x] 验证调用顺序正确
  - [x] 测试不支持的文件格式 → 抛出 ValueError
  - [x] 测试空文档（返回 0）
  - [x] 测试 sections 透传到 splitter
  - [x] 测试 .pdf 和 .md 扩展名正确处理
- [x] 创建 `backend/app/rag/tests/conftest.py`
  - [x] Fixture：所有 Mock 组件
  - [x] Fixture：DocumentPipeline 实例

### 3. 验证

- [x] Pipeline 编排正确
- [x] 各组件调用顺序符合设计
- [x] `pytest backend/app/rag/tests/` 全部通过

---

## v2 重构说明

原来的 `DocumentPipeline` 直接持有 `ParserRouter` + `TextSplitter`，所有文档类型共用一个 splitter，导致 `ParsedDocument.sections` 完全闲置。

v2 版本引入了 **StrategyRouter + ChunkingStrategy** 机制：

```
                    ┌──────────────────────────────┐
                    │     StrategyRouter            │
                    │  .txt    → TextStrategy       │
                    │  .md     → MarkdownStrategy   │
                    │  .pdf    → PDFStrategy        │
                    │  .docx   → DocxStrategy       │
                    └──────────┬───────────────────┘
                               │ get_strategy(ext)
                               ▼
                    ┌──────────────────────────────┐
                    │     ChunkingStrategy          │
                    │  - parser (按文档类型选择)     │
                    │  - splitter (按文档类型选择)   │
                    │  - execute() → parse + split │
                    └──────────────────────────────┘
```

每个文档类型配有自己专门的 (parser, splitter) 配对，splitter 能直接消费 parser 产出的 `sections` 结构化数据。

### 策略对照

| 扩展名 | 策略名 | 解析器 | 切片器 | sections 利用 |
|--------|--------|--------|--------|--------------|
| .txt / .text | text | TextParser | FixedSizeSplitter | ❌ 不感知 |
| .md / .markdown | markdown | TextParser | MarkdownSplitter | ✅ heading 层级 |
| .pdf | pdf | PDFParser | PDFPageSplitter | ✅ page 编号 |
| .docx | docx | DocxParser | FixedSizeSplitter | ❌ 不感知（预留） |

---

## 验收标准

- [x] Pipeline 不包含任何实现细节（只编排）
- [x] 每个步骤间的数据传递类型正确
- [x] 错误传播清晰（解析失败 → 抛出异常）
- [x] 返回切片数量
- [x] sections 数据被有效利用（Markdown + PDF）
