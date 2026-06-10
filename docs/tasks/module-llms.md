# M13：LLM 模块 (rag/llms)

**阶段**: Phase 3 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M01 Config、M08 Interfaces

**参考设计**: [详细设计文档 Module-13](../详细设计文档.md#module-13-llm-模块-ragllms)

---

## 任务清单

### 1. DeepSeekLLM

- [x] 创建 `backend/app/rag/llms/__init__.py`
- [x] 创建 `backend/app/rag/llms/deepseek_llm.py`
  - [x] `DeepSeekLLM(LLMBackend)`
  - [x] `__init__(api_key, model="deepseek-chat", base_url="https://api.deepseek.com")`
    - [x] 使用 `AsyncOpenAI` 客户端（兼容 OpenAI API）
  - [x] `async generate(messages, temperature, max_tokens) -> str`
    - [x] 调用非流式接口
    - [x] 处理空响应（返回 `""`）
  - [x] `async generate_stream(messages, temperature, max_tokens) -> AsyncIterator[str]`
    - [x] 调用流式接口，逐 token yield
  - [x] `model_name -> str` 返回 `"deepseek/{model_name}"`

### 2. OpenAILLM（预留）

- [x] 创建 `backend/app/rag/llms/openai_llm.py`（可立即实现，与 DeepSeekLLM 结构几乎一致）
  - [x] `OpenAILLM(LLMBackend)`
  - [x] 实现同上，但使用 OpenAI 的 base_url

### 3. OllamaLLM（预留）

- [x] 创建 `backend/app/rag/llms/ollama_llm.py`（占位）

### 4. 测试

- [x] 创建 `backend/app/rag/llms/tests/__init__.py`
- [x] 创建 `backend/app/rag/llms/tests/test_deepseek_llm.py`
  - [x] 使用 Mock HTTP 请求
  - [x] 测试非流式生成 → 返回字符串
  - [x] 测试流式生成 → 逐 token 发送
  - [x] 测试 API 返回空内容 → 返回空字符串
  - [x] 测试 HTTP 错误 → 异常处理
- [x] 创建 `backend/app/rag/llms/tests/test_openai_llm.py`
  - [x] 同样使用 Mock
  - [x] 测试基础功能

### 5. 验证

- [x] LLM 接口调用正常（Mock 验证通过）
- [x] 流式接口 yield 正确
- [x] `pytest backend/app/rag/llms/tests/` 全部通过

---

## 验收标准

- [x] DeepSeek API 接入正常（流式 + 非流式）
- [x] OpenAI API 兼容（通过 AsyncOpenAI 客户端）
- [x] 实现可替换（通过接口）
- [x] API 调用失败时不会直接崩溃
