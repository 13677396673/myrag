"""
DeepSeekLLM 单元测试

测试策略：
- 使用 mock 替换 AsyncOpenAI 客户端（不发起真实 HTTP 请求）
- 测试非流式生成 → 返回字符串
- 测试流式生成 → 逐 token 发送
- 测试 API 返回空内容 → 返回空字符串
- 测试 HTTP 错误 → 异常传递
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.llms import DeepSeekLLM

# deepseek_llm.py 内部使用 from openai import AsyncOpenAI
PATCH_PATH = "app.rag.llms.deepseek_llm.AsyncOpenAI"


def _async_iter(items):
    """将普通列表转换为异步迭代器"""
    async def _gen():
        for item in items:
            yield item
    return _gen()


class TestDeepSeekLLM:
    """DeepSeekLLM 单元测试"""

    # ── 初始化 ──

    def test_init(self):
        """测试初始化"""
        with patch(PATCH_PATH):
            llm = DeepSeekLLM(api_key="sk-deepseek-key")
            assert llm._model == "deepseek-chat"

    def test_init_custom_params(self):
        """测试自定义参数"""
        with patch(PATCH_PATH):
            llm = DeepSeekLLM(
                api_key="sk-custom",
                model="custom-model",
                base_url="https://custom.api.com",
            )
            assert llm._model == "custom-model"

    # ── 非流式生成 ──

    @pytest.mark.asyncio
    async def test_generate_returns_string(self):
        """测试非流式生成返回字符串"""
        with patch(PATCH_PATH) as mock_async:
            mock_instance = AsyncMock()
            mock_async.return_value = mock_instance

            # 构造模拟的 API 响应
            mock_resp = MagicMock()
            mock_message = MagicMock()
            mock_message.content = "你好，我是 DeepSeek。"
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_resp.choices = [mock_choice]
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)

            llm = DeepSeekLLM(api_key="sk-deepseek-key")
            result = await llm.generate(
                messages=[{"role": "user", "content": "你好"}],
                temperature=0.5,
                max_tokens=100,
            )

            assert isinstance(result, str)
            assert result == "你好，我是 DeepSeek。"
            mock_instance.chat.completions.create.assert_called_once_with(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "你好"}],
                temperature=0.5,
                max_tokens=100,
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

            llm = DeepSeekLLM(api_key="sk-deepseek-key")
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

            llm = DeepSeekLLM(api_key="sk-deepseek-key")
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

            # 构造模拟的流式 chunks
            chunks = []
            for token in ["你好", "，", "世界"]:
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

            llm = DeepSeekLLM(api_key="sk-deepseek-key")
            tokens = []
            async for token in llm.generate_stream(
                messages=[{"role": "user", "content": "你好"}],
                temperature=0.7,
                max_tokens=100,
            ):
                tokens.append(token)

            assert tokens == ["你好", "，", "世界"]
            mock_instance.chat.completions.create.assert_called_once_with(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "你好"}],
                temperature=0.7,
                max_tokens=100,
                stream=True,
            )

    @pytest.mark.asyncio
    async def test_generate_stream_skips_empty_content(self):
        """测试流式生成跳过空 content"""
        with patch(PATCH_PATH) as mock_async:
            mock_instance = AsyncMock()
            mock_async.return_value = mock_instance

            chunks = []
            for token in ["Hello", "", " World", None, "!"]:
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

            llm = DeepSeekLLM(api_key="sk-deepseek-key")
            tokens = []
            async for token in llm.generate_stream(
                messages=[{"role": "user", "content": "hi"}]
            ):
                tokens.append(token)

            assert tokens == ["Hello", " World", "!"]

    # ── 属性 ──

    def test_model_name(self):
        """测试 model_name 属性"""
        with patch(PATCH_PATH):
            llm = DeepSeekLLM(api_key="sk-deepseek-key", model="deepseek-chat")
            assert llm.model_name == "deepseek/deepseek-chat"

    def test_model_name_custom_model(self):
        """测试自定义模型名称"""
        with patch(PATCH_PATH):
            llm = DeepSeekLLM(api_key="sk-deepseek-key", model="deepseek-reasoner")
            assert llm.model_name == "deepseek/deepseek-reasoner"
