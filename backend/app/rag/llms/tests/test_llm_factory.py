"""
create_llm 工厂函数单元测试

测试内容：
- 根据配置正确创建 DeepSeekLLM
- 根据配置正确创建 OpenAILLM
- 缺少 API Key 时抛出 ValueError
- 不支持的后端抛出 ValueError
"""

from unittest.mock import patch

import pytest

from app.rag.llms import create_llm


class MockSettings:
    """模拟 Settings 对象用于工厂测试"""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestCreateLLMFactory:
    """create_llm 工厂函数测试"""

    def test_create_deepseek(self):
        """测试创建 DeepSeekLLM"""
        settings = MockSettings(
            LLM_BACKEND="deepseek",
            DEEPSEEK_API_KEY="sk-deepseek-key",
            DEEPSEEK_MODEL="deepseek-chat",
            DEEPSEEK_BASE_URL="https://api.deepseek.com",
            OPENAI_API_KEY=None,
        )

        with patch("app.rag.llms.deepseek_llm.AsyncOpenAI"):
            llm = create_llm(settings)
            from app.rag.llms import DeepSeekLLM
            assert isinstance(llm, DeepSeekLLM)
            assert llm._model == "deepseek-chat"

    def test_create_deepseek_missing_key_raises(self):
        """测试 DeepSeek 缺少 API Key 时抛出异常"""
        settings = MockSettings(
            LLM_BACKEND="deepseek",
            DEEPSEEK_API_KEY=None,
            DEEPSEEK_MODEL="deepseek-chat",
            DEEPSEEK_BASE_URL="https://api.deepseek.com",
        )

        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            create_llm(settings)

    def test_create_openai(self):
        """测试创建 OpenAILLM"""
        settings = MockSettings(
            LLM_BACKEND="openai",
            OPENAI_API_KEY="sk-openai-key",
            OPENAI_MODEL="gpt-4o-mini",
            OPENAI_BASE_URL="https://api.openai.com/v1",
        )

        with patch("app.rag.llms.openai_llm.AsyncOpenAI"):
            llm = create_llm(settings)
            from app.rag.llms import OpenAILLM
            assert isinstance(llm, OpenAILLM)
            assert llm._model == "gpt-4o-mini"

    def test_create_openai_missing_key_raises(self):
        """测试 OpenAI 缺少 API Key 时抛出异常"""
        settings = MockSettings(
            LLM_BACKEND="openai",
            OPENAI_API_KEY=None,
            OPENAI_MODEL="gpt-4o-mini",
            OPENAI_BASE_URL="https://api.openai.com/v1",
        )

        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            create_llm(settings)

    def test_ollama_not_implemented_raises(self):
        """测试 Ollama 尚未实现时抛出异常"""
        settings = MockSettings(LLM_BACKEND="ollama")

        with pytest.raises(ValueError, match="尚未实现"):
            create_llm(settings)

    def test_unsupported_backend_raises(self):
        """测试不支持的后端抛出异常"""
        settings = MockSettings(LLM_BACKEND="unknown")

        with pytest.raises(ValueError, match="不支持的"):
            create_llm(settings)
