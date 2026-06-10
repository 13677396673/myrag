"""
OpenAILLM 单元测试

测试策略：
- 使用 mock 替换 AsyncOpenAI 客户端
- 测试非流式生成 → 返回字符串
- 测试流式生成 → 逐 token 发送
- 测试 API 返回空内容 → 返回空字符串
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.llms import OpenAILLM

# openai_llm.py 内部使用 from openai import AsyncOpenAI
PATCH_PATH = "app.rag.llms.openai_llm.AsyncOpenAI"


def _async_iter(items):
    """将普通列表转换为异步迭代器"""
    async def _gen():
        for item in items:
            yield item
    return _gen()


class TestOpenAILLM:
    """OpenAILLM 单元测试"""

    # ── 初始化 ──

    def test_init(self):
        """测试初始化"""
        with patch(PATCH_PATH):
            llm = OpenAILLM(api_key="sk-openai-key")
            assert llm._model == "gpt-4o-mini"

    def test_init_custom_params(self):
        """测试自定义参数"""
        with patch(PATCH_PATH):
            llm = OpenAILLM(
                api_key="sk-custom",
                model="gpt-4o",
                base_url="https://custom.api.com/v1",
            )
            assert llm._model == "gpt-4o"

    # ── 非流式生成 ──

    @pytest.mark.asyncio
    async def test_generate_returns_string(self):
        """测试非流式生成返回字符串"""
        with patch(PATCH_PATH) as mock_async:
            mock_instance = AsyncMock()
            mock_async.return_value = mock_instance

            mock_resp = MagicMock()
            mock_message = MagicMock()
            mock_message.content = "Hello! How can I help?"
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_resp.choices = [mock_choice]
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)

            llm = OpenAILLM(api_key="sk-openai-key")
            result = await llm.generate(
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert result == "Hello! How can I help?"
            mock_instance.chat.completions.create.assert_called_once_with(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.7,
                max_tokens=2048,
                stream=False,
            )

    @pytest.mark.asyncio
    async def test_generate_empty_content_returns_empty_string(self):
        """测试 API 返回空内容时返回空字符串"""
        with patch(PATCH_PATH) as mock_async:
            mock_instance = AsyncMock()
            mock_async.return_value = mock_instance

            mock_resp = MagicMock()
            mock_message = MagicMock()
            mock_message.content = None
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_resp.choices = [mock_choice]
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)

            llm = OpenAILLM(api_key="sk-openai-key")
            result = await llm.generate(
                messages=[{"role": "user", "content": "test"}]
            )
            assert result == ""

    @pytest.mark.asyncio
    async def test_generate_empty_choices_returns_empty_string(self):
        """测试 API 返回空 choices 时返回空字符串"""
        with patch(PATCH_PATH) as mock_async:
            mock_instance = AsyncMock()
            mock_async.return_value = mock_instance

            mock_resp = MagicMock()
            mock_resp.choices = []
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)

            llm = OpenAILLM(api_key="sk-openai-key")
            result = await llm.generate(
                messages=[{"role": "user", "content": "test"}]
            )
            assert result == ""

    # ── 流式生成 ──

    @pytest.mark.asyncio
    async def test_generate_stream_yields_tokens(self):
        """测试流式生成逐 token yield"""
        with patch(PATCH_PATH) as mock_async:
            mock_instance = AsyncMock()
            mock_async.return_value = mock_instance

            chunks = []
            for token in ["Hello", " ", "World"]:
                chunk = MagicMock()
                delta = MagicMock()
                delta.content = token
                choice = MagicMock()
                choice.delta = delta
                chunk.choices = [choice]
                chunks.append(chunk)

            mock_instance.chat.completions.create = AsyncMock(
                return_value=_async_iter(chunks)
            )

            llm = OpenAILLM(api_key="sk-openai-key")
            tokens = []
            async for token in llm.generate_stream(
                messages=[{"role": "user", "content": "Hello"}],
            ):
                tokens.append(token)

            assert tokens == ["Hello", " ", "World"]

    @pytest.mark.asyncio
    async def test_generate_stream_skips_empty_content(self):
        """测试流式生成跳过空 content"""
        with patch(PATCH_PATH) as mock_async:
            mock_instance = AsyncMock()
            mock_async.return_value = mock_instance

            chunks = []
            for token in ["Hi", None, "", " there"]:
                chunk = MagicMock()
                delta = MagicMock()
                delta.content = token
                choice = MagicMock()
                choice.delta = delta
                chunk.choices = [choice]
                chunks.append(chunk)

            mock_instance.chat.completions.create = AsyncMock(
                return_value=_async_iter(chunks)
            )

            llm = OpenAILLM(api_key="sk-openai-key")
            tokens = []
            async for token in llm.generate_stream(
                messages=[{"role": "user", "content": "hi"}]
            ):
                tokens.append(token)

            assert tokens == ["Hi", " there"]

    # ── 属性 ──

    def test_model_name(self):
        """测试 model_name 属性"""
        with patch(PATCH_PATH):
            llm = OpenAILLM(api_key="sk-openai-key", model="gpt-4o-mini")
            assert llm.model_name == "openai/gpt-4o-mini"

    def test_model_name_custom_model(self):
        """测试自定义模型名称"""
        with patch(PATCH_PATH):
            llm = OpenAILLM(api_key="sk-openai-key", model="gpt-4o")
            assert llm.model_name == "openai/gpt-4o"
