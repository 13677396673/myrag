# M16：RAG 引擎模块 (rag/rag_engine)

**阶段**: Phase 4 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M14 Retriever、M13 LLM

**参考设计**: [详细设计文档 Module-16](../详细设计文档.md#module-16-rag-引擎模块-ragrag_engine)

---

## 任务清单

### 1. RAGEngine 类

- [x] 创建 `backend/app/rag/rag_engine.py`
  - [x] `RAGEngine` 类
  - [x] `__init__(retriever: Retriever, llm: LLMBackend)`
  - [x] 定义 `SYSTEM_PROMPT_TEMPLATE`（包含 context 占位符和回答规则）
  - [x] `_format_context(results: List[SearchResult]) -> str`
    - [x] 格式：`[1] content1\n\n[2] content2\n\n...`
  - [x] `_build_messages(question, context, history) -> List[dict]`
    - [x] 系统 prompt + 历史（最近 20 条）+ 当前问题
    - [x] 历史消息保留 role/content 结构
  - [x] `async query(question, history, top_k, filter_conditions) -> dict`
    - [x] 步骤：检索 → 上下文 → 组装 messages → LLM 生成 → 返回 {answer, sources}
  - [x] `async query_stream(question, history, top_k, filter_conditions) -> AsyncIterator[dict]`
    - [x] yield `{"type": "sources", "content": [...]}`（检索结果）
    - [x] yield `{"type": "delta", "content": token}`（LLM 流式输出）
    - [x] yield `{"type": "done"}`（完成）

### 2. 测试

- [x] 创建 `backend/app/rag/tests/test_rag_engine.py`
  - [x] Mock `Retriever`
  - [x] Mock `LLMBackend`（非流式 + 流式均 Mock）
  - [x] 测试 `query()` — 非流式查询
    - [x] 验证 LLM.generate 被调用
    - [x] 验证返回格式包含 answer 和 sources
  - [x] 测试 `query_stream()` — 流式查询
    - [x] 验证 yield 顺序：sources → delta(s) → done
  - [x] 测试无检索结果时的行为
  - [x] 测试历史消息传递
  - [x] 测试 `_build_messages` 正确组装多个历史轮次
  - [x] 测试 filter_conditions 透传给 retriever
- [x] 创建 `backend/app/rag/tests/conftest.py`（更新）
  - [x] Fixture：Mock Retriever
  - [x] Fixture：Mock LLM
  - [x] Fixture：RAGEngine 实例

### 3. 验证

- [x] 完整 RAG 流程可运行
- [x] 流式和非流式两种模式都能工作
- [x] `pytest backend/app/rag/tests/test_rag_engine.py` 全部通过

---

## 验收标准

- [x] 引擎通过注入组合 Retriever + LLM
- [x] 系统 Prompt 包含回答规则（不编造、引用来源、中文回答）
- [x] 历史消息正确传递
- [x] 流式输出严格按照 sources → delta → done 顺序
- [x] 无检索结果时正常降级
