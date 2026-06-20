# M26：文档 Chunking 策略模块 (rag/strategies)

**阶段**: Phase 4 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M08 Interfaces、M09 Parsers、M10 Splitters

**参考设计**: [详细设计文档](../详细设计文档.md)

---

## 概述

`rag/strategies` 是 v2 新增的模块，实现了 RagFlow 风格的多策略路由架构。
它将 `ParserRouter` + `TextSplitter` 的松散组合升级为**按文档类型配对的策略系统**，
使 `ParsedDocument.sections` 中的结构化信息能被 splitter 有效利用。

## 核心概念

### ChunkingStrategy

将 `DocumentParser` 和 `TextSplitter` 配对，表示一种文档类型的完整处理策略。

```python
@dataclass
class ChunkingStrategy:
    name: str          # 策略名称，如 "markdown", "pdf", "text"
    parser: DocumentParser    # 文档解析器
    splitter: TextSplitter    # 文本切片器
    description: str = ""

    def execute(self, file_path: str, metadata: dict) -> List[DocumentChunk]:
        """执行解析 + 切分"""
```

### StrategyRouter

根据文件扩展名路由到对应的 `ChunkingStrategy`。

```python
class StrategyRouter:
    def register(self, extensions: List[str], strategy: ChunkingStrategy) -> None
    def get_strategy(self, ext: str) -> Optional[ChunkingStrategy]
    def get_supported_extensions(self) -> List[str]
```

## 内置策略

| 扩展名 | 策略名 | 解析器 | 切片器 | sections 消费 |
|--------|--------|--------|--------|--------------|
| .txt / .text | text | TextParser | FixedSizeSplitter | ❌ 忽略 |
| .md / .markdown | markdown | TextParser（含 heading 解析） | MarkdownSplitter | ✅ heading 层级 |
| .pdf | pdf | PDFParser（已有 page sections） | PDFPageSplitter | ✅ page 编号 |
| .docx | docx | DocxParser | FixedSizeSplitter | ❌ 忽略 |

## 数据流

```
register_default_strategies(router)
         │
         ▼
StrategyRouter
  .txt ──► TextStrategy ──► TextParser.parse() ──► sections=[] ──► FixedSizeSplitter.split()
  .md  ──► MarkdownStrategy ──► TextParser.parse() ──► sections=[{heading, level, content}] ──► MarkdownSplitter.split()
  .pdf ──► PDFStrategy ──► PDFParser.parse() ──► sections=[{page, content}] ──► PDFPageSplitter.split()
  .docx──► DocxStrategy ──► DocxParser.parse() ──► sections=[] ──► FixedSizeSplitter.split()
```

## 注册

```python
from app.rag.strategies import StrategyRouter, register_default_strategies

router = StrategyRouter()
register_default_strategies(
    router,
    chunk_size=512,
    chunk_overlap=64,
)
```

## 与旧架构的对比

| 维度 | v1（旧） | v2（新） |
|------|----------|----------|
| Pipeline 构造参数 | `parser_router` + `splitter` | `strategy_router` |
| 文档类型选择 | 仅 parser 按扩展名选择 | parser + splitter 配对选择 |
| sections 利用 | 完全闲置 | Markdown/pPDF 策略使用 |
| 扩展新文档类型 | 加 parser，splitter 通用 | 加新策略，parser+splitter 同时定制 |

## 文件清单

```
backend/app/rag/strategies/
├── __init__.py        # 导出 ChunkingStrategy, StrategyRouter, register_default_strategies
├── base.py            # ChunkingStrategy 数据类 + execute 方法
├── router.py          # StrategyRouter 路由
└── defaults.py        # register_default_strategies 注册函数
```
