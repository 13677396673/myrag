# M13：LLM 模块 (rag/llms)

**阶段**: Phase 3 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M01 Config、M08 Interfaces

**参考设计**: [详细设计文档 Module-13](../详细设计文档.md#module-13-llm-模块-ragllms)

---

## 任务清单

### 1. DeepSeekLLM

- [ ] 创建 `backend/app/rag/llms/__init__.py`
- [ ] 创建 `backend/app/rag/llms/deepseek_llm.py`
  - [ ] `DeepSeekLLM(LLMBackend)`
  - [ ] `__init__(api_key, model="deepseek-chat", base_url="https://api.deepseek.com")`
    - [ ] 使用 `AsyncOpenAI` 客户端（兼容 OpenAI API）
  - [ ] `async generate(messages, temperature, max_tokens) -> str`
    - [ ] 调用非流式接口
    - [ ] 处理空响应（返回 `""`）
  - [ ] `async generate_stream(messages, temperature, max_tokens) -> AsyncIterator[str]`
    - [ ] 调用流式接口，逐 token yield
  - [ ] `model_name -> str` 返回 `"deepseek/{model_name}"`

### 2. OpenAILLM（预留）

- [ ] 创建 `backend/app/rag/llms/openai_llm.py`（可立即实现，与 DeepSeekLLM 结构几乎一致）
  - [ ] `OpenAILLM(LLMBackend)`
  - [ ] 实现同上，但使用 OpenAI 的 base_url

### 3. OllamaLLM（预留）

- [ ] 创建 `backend/app/rag/llms/ollama_llm.py`（占位）

### 4. 测试

- [ ] 创建 `backend/app/rag/llms/tests/__init__.py`
- [ ] 创建 `backend/app/rag/llms/tests/test_deepseek_llm.py`
  - [ ] 使用 `pytest-httpx` Mock HTTP 请求
  - [ ] 测试非流式生成 → 返回字符串
  - [ ] 测试流式生成 → 逐 token 发送
  - [ ] 测试 API 返回空内容 → 返回空字符串
  - [ ] 测试 HTTP 错误 → 异常处理
- [ ] 创建 `backend/app/rag/llms/tests/test_openai_llm.py`
  - [ ] 同样使用 Mock HTTP
  - [ ] 测试基础功能

### 5. 验证

- [ ] LLM 接口调用正常（需 DEEPSEEK_API_KEY）
- [ ] 流式接口 yield 正确
- [ ] `pytest backend/app/rag/llms/tests/` 全部通过

---

## 验收标准

- [ ] DeepSeek API 接入正常（流式 + 非流式）
- [ ] OpenAI API 兼容（通过 AsyncOpenAI 客户端）
- [ ] 实现可替换（通过接口）
- [ ] API 调用失败时不会直接崩溃
