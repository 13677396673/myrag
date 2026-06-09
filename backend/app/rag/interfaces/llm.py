from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator


class LLMBackend(ABC):
    """大语言模型抽象接口"""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        非流式生成完整回复。

        参数:
            messages: 消息列表，如 [{"role": "user", "content": "..."}]
            temperature: 生成温度，控制随机性 (0.0 ~ 2.0)
            max_tokens: 最大生成 token 数

        返回:
            模型生成的文本内容
        """
        ...

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """
        流式生成，每次 yield 一个 token 字符串。
        调用方负责组装完整的响应。

        参数:
            messages: 消息列表
            temperature: 生成温度
            max_tokens: 最大生成 token 数

        返回:
            异步迭代器，每次 yield 一个 token 片段
        """
        ...
        # 此处 yield 语句使方法成为异步生成器
        yield ""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回当前模型名称"""
        ...
