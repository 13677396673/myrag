"""DeepSeek LLM 实现

使用 OpenAI 兼容 SDK（``AsyncOpenAI``）调用 DeepSeek API，
支持流式和非流式生成。

用法::

    from app.rag.llms import DeepSeekLLM

    llm = DeepSeekLLM(api_key="sk-xxx")
    reply = await llm.generate([{"role": "user", "content": "你好"}])
    print(reply)
"""

from typing import List, Dict, Any, AsyncIterator

from openai import AsyncOpenAI

from app.rag.interfaces.llm import LLMBackend


class DeepSeekLLM(LLMBackend):
    """DeepSeek API 大语言模型实现

    通过 ``AsyncOpenAI`` 客户端调用 DeepSeek 兼容接口，
    支持流式（SSE）和非流式两种生成模式。

    参数:
        api_key: DeepSeek API 密钥
        model: 模型名称，默认 ``"deepseek-chat"``
        base_url: API 基础地址，默认 ``https://api.deepseek.com``
    """

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
    ):
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """非流式生成完整回复

        参数:
            messages: 消息列表，如 [{"role": "user", "content": "你好"}]
            temperature: 生成温度 (0.0 ~ 2.0)
            max_tokens: 最大生成 token 数

        返回:
            模型生成的文本内容；API 返回空内容时返回 ``""``
        """
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        choice = resp.choices[0] if resp.choices else None
        return choice.message.content or "" if choice else ""

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """流式生成，每次 yield 一个 token 片段

        参数:
            messages: 消息列表
            temperature: 生成温度
            max_tokens: 最大生成 token 数

        Yields:
            token 片段字符串；API 流中跳过空内容
        """
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    @property
    def model_name(self) -> str:
        """返回模型名称，格式 ``deepseek/{model}``"""
        return f"deepseek/{self._model}"
