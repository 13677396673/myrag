# M16：RAG 引擎模块 (rag/rag_engine)

**阶段**: Phase 4 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M14 Retriever、M13 LLM

**参考设计**: [详细设计文档 Module-16](../详细设计文档.md#module-16-rag-引擎模块-ragrag_engine)

---

## 任务清单

### 1. RAGEngine 类

- [ ] 创建 `backend/app/rag/rag_engine.py`
  - [ ] `RAGEngine` 类
  - [ ] `__init__(retriever: Retriever, llm: LLMBackend)`
  - [ ] 定义 `SYSTEM_PROMPT_TEMPLATE`（包含 context 占位符和回答规则）
  - [ ] `_format_context(results: List[SearchResult]) -> str`
    - [ ] 格式：`[1] content1\n\n[2] content2\n\n...`
  - [ ] `_build_messages(question, context, history) -> List[dict]`
    - [ ] 系统 prompt + 历史（最近 20 条）+ 当前问题
    - [ ] 历史消息保留 role/content 结构
  - [ ] `async query(question, history, top_k, filter_conditions) -> dict`
    - [ ] 步骤：检索 → 上下文 → 组装 messages → LLM 生成 → 返回 {answer, sources}
  - [ ] `async query_stream(question, history, top_k, filter_conditions) -> AsyncIterator[dict]`
    - [ ] yield `{"type": "sources", "content": [...]}`（检索结果）
    - [ ] yield `{"type": "delta", "content": token}`（LLM 流式输出）
    - [ ] yield `{"type": "done"}`（完成）

### 2. 测试

- [ ] 创建 `backend/app/rag/tests/test_rag_engine.py`
  - [ ] Mock `Retriever`
  - [ ] Mock `LLMBackend`（非流式 + 流式均 Mock）
  - [ ] 测试 `query()` — 非流式查询
    - [ ] 验证 LLM.generate 被调用
    - [ ] 验证返回格式包含 answer 和 sources
  - [ ] 测试 `query_stream()` — 流式查询
    - [ ] 验证 yield 顺序：sources → delta(s) → done
  - [ ] 测试无检索结果时的行为
  - [ ] 测试历史消息传递
  - [ ] 测试 `_build_messages` 正确组装多个历史轮次
  - [ ] 测试 filter_conditions 透传给 retriever
- [ ] 创建 `backend/app/rag/tests/conftest.py`（更新）
  - [ ] Fixture：Mock Retriever
  - [ ] Fixture：Mock LLM
  - [ ] Fixture：RAGEngine 实例

### 3. 验证

- [ ] 完整 RAG 流程可运行
- [ ] 流式和非流式两种模式都能工作
- [ ] `pytest backend/app/rag/tests/test_rag_engine.py` 全部通过

---

## 验收标准

- [ ] 引擎通过注入组合 Retriever + LLM
- [ ] 系统 Prompt 包含回答规则（不编造、引用来源、中文回答）
- [ ] 历史消息正确传递
- [ ] 流式输出严格按照 sources → delta → done 顺序
- [ ] 无检索结果时正常降级
