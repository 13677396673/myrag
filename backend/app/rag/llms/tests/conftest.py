"""pytest fixtures for LLM tests"""

from unittest.mock import MagicMock, AsyncMock

import pytest


def make_mock_chunk(content: str) -> MagicMock:
    """创建一个模拟的流式 chunk

    模拟 ``openai.types.chat.ChatCompletionChunk`` 的结构：
    ``chunk.choices[0].delta.content``
    """
    chunk = MagicMock()
    delta = MagicMock()
    delta.content = content
    choice = MagicMock()
    choice.delta = delta
    choice.index = 0
    chunk.choices = [choice]
    return chunk


def make_mock_nonstream_response(content: str) -> MagicMock:
    """创建一个模拟的非流式响应

    模拟 ``openai.types.chat.ChatCompletion`` 的结构：
    ``resp.choices[0].message.content``
    """
    resp = MagicMock()
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    choice.index = 0
    resp.choices = [choice]
    return resp


@pytest.fixture
def mock_openai_client():
    """Mock ``openai.AsyncOpenAI`` 客户端

    返回一个 ``(mock_client_class, mock_client_instance)`` 二元组，
    测试可对 ``mock_client.chat.completions.create`` 设置返回值。
    """
    with __import__("unittest.mock").patch("openai.AsyncOpenAI") as mock_async:
        mock_instance = AsyncMock()
        mock_async.return_value = mock_instance
        yield mock_async, mock_instance
