# M09：文档解析器模块 (rag/parsers)

**阶段**: Phase 3 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M08 Interfaces

**参考设计**: [详细设计文档 Module-09](../详细设计文档.md#module-09-文档解析器模块-ragparsers)

---

## 任务清单

### 1. ParserRouter

- [ ] 创建 `backend/app/rag/parsers/__init__.py`
- [ ] 创建 `backend/app/rag/parsers/parser_router.py`
  - [ ] `ParserRouter` 类
  - [ ] `__init__()` — 初始化 `_registry: Dict[str, Type[DocumentParser]]`
  - [ ] `register(parser_cls: Type[DocumentParser])` — 注册解析器
  - [ ] `get_parser(extension: str) -> Optional[DocumentParser]` — 获取解析器实例
  - [ ] `get_supported_extensions() -> List[str]` — 列出所有支持扩展名

### 2. TextParser

- [ ] 创建 `backend/app/rag/parsers/text_parser.py`
  - [ ] `TextParser(DocumentParser)`
  - [ ] `parse(file_path)` — 读取 txt/md 内容
  - [ ] `supported_extensions()` — 返回 `[.txt, .md, .text, .markdown]`
  - [ ] 使用 `encoding="utf-8"` 打开文件，`errors="replace"` 处理编码问题

### 3. PDFParser

- [ ] 创建 `backend/app/rag/parsers/pdf_parser.py`
  - [ ] `PDFParser(DocumentParser)`
  - [ ] `parse(file_path)` — 使用 PyMuPDF (fitz) 逐页提取
  - [ ] `supported_extensions()` — 返回 `[.pdf]`
  - [ ] 提取每页文本，返回含页码的 sections

### 4. DocxParser

- [ ] 创建 `backend/app/rag/parsers/docx_parser.py`
  - [ ] `DocxParser(DocumentParser)`
  - [ ] `parse(file_path)` — 使用 python-docx 提取
  - [ ] `supported_extensions()` — 返回 `[.docx]`
  - [ ] 提取段落文本，用 `\n\n` 连接

### 5. 注册内置解析器

- [ ] 在 `parsers/__init__.py` 中定义 `register_default_parsers(router: ParserRouter)`
  - [ ] 注册 TextParser
  - [ ] 注册 PDFParser
  - [ ] 注册 DocxParser
- [ ] `__all__` 导出：ParserRouter、TextParser、PDFParser、DocxParser、register_default_parsers

### 6. 预留解析器占位

- [ ] 创建 `backend/app/rag/parsers/pptx_parser.py`（占位，含 `# 预留` 注释）
- [ ] 创建 `backend/app/rag/parsers/xlsx_parser.py`（占位）
- [ ] 创建 `backend/app/rag/parsers/ocr_parser.py`（占位）
- [ ] 创建 `backend/app/rag/parsers/web_parser.py`（占位）

### 7. 测试

- [ ] 创建 `backend/app/rag/parsers/tests/__init__.py`
- [ ] 创建测试夹具文件：
  - [ ] `backend/app/rag/parsers/tests/fixtures/sample.txt` — 少量文本
  - [ ] `backend/app/rag/parsers/tests/fixtures/sample.md` — Markdown 内容
  - [ ] `backend/app/rag/parsers/tests/fixtures/sample.pdf` — 2-3 页文字 PDF
  - [ ] `backend/app/rag/parsers/tests/fixtures/sample.docx` — 含标题的文档
- [ ] 创建 `backend/app/rag/parsers/tests/test_text_parser.py`
  - [ ] 测试 .txt 文件解析
  - [ ] 测试 .md 文件解析
  - [ ] 测试空文件解析
  - [ ] 验证 ParsedDocument 结构正确
- [ ] 创建 `backend/app/rag/parsers/tests/test_pdf_parser.py`
  - [ ] 测试 PDF 解析，验证 content 不为空
  - [ ] 验证 sections 包含页码信息
  - [ ] 测试不支持的文件 → 正常解析（PDFParser 只管 .pdf 后缀的文件）
- [ ] 创建 `backend/app/rag/parsers/tests/test_docx_parser.py`
  - [ ] 测试 .docx 解析
  - [ ] 验证段落提取
- [ ] 创建 `backend/app/rag/parsers/tests/test_parser_router.py`
  - [ ] 测试注册解析器
  - [ ] 测试根据扩展名正确路由
  - [ ] 测试不支持的扩展名返回 None
- [ ] 创建 `backend/app/rag/parsers/tests/conftest.py`
  - [ ] Fixture：各个夹具文件的路径
  - [ ] Fixture：注册了默认解析器的 ParserRouter

### 8. 验证

- [ ] 所有解析器可独立测试
- [ ] 中文和英文内容均可正确提取
- [ ] `pytest backend/app/rag/parsers/tests/` 全部通过

---

## 验收标准

- [ ] ParserRouter 支持动态注册解析器
- [ ] TXT/MD 解析无强依赖（Python 内置）
- [ ] PDF 解析依赖 PyMuPDF
- [ ] DOCX 解析依赖 python-docx
- [ ] 每个解析器独立文件、独立测试
- [ ] 不支持的格式优雅返回 None（不抛异常）
