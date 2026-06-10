"""LLM 模块

提供 ``DeepSeekLLM``（DeepSeek API）、``OpenAILLM``（OpenAI API）
两种 LLM 实现，以及 ``create_llm`` 工厂函数用于根据配置自动选择。

用法::

    from app.config import settings
    from app.rag.llms import create_llm

    llm = create_llm(settings)

    # 或直接实例化
    from app.rag.llms import DeepSeekLLM
    llm = DeepSeekLLM(api_key="sk-xxx")
    reply = await llm.generate([{"role": "user", "content": "你好"}])
"""

from .deepseek_llm import DeepSeekLLM
from .openai_llm import OpenAILLM

__all__ = [
    "DeepSeekLLM",
    "OpenAILLM",
    "create_llm",
]


def create_llm(settings) -> "DeepSeekLLM | OpenAILLM":
    """根据配置创建 LLM 后端实例

    依据 ``settings.LLM_BACKEND`` 的值选择实现：

    - ``deepseek`` → 创建 ``DeepSeekLLM``
    - ``openai`` → 创建 ``OpenAILLM``
    - ``ollama`` → 抛出 ``ValueError``（尚未实现）

    参数:
        settings: 应用配置对象（``app.config.Settings``）

    返回:
        实现了 ``LLMBackend`` 接口的实例

    异常:
        ValueError: 不支持的 ``LLM_BACKEND`` 值或未实现的占位后端
    """
    backend = settings.LLM_BACKEND

    if backend == "deepseek":
        if not settings.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY 未配置，无法创建 DeepSeekLLM")
        return DeepSeekLLM(
            api_key=settings.DEEPSEEK_API_KEY,
            model=settings.DEEPSEEK_MODEL,
            base_url=settings.DEEPSEEK_BASE_URL,
        )

    if backend == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置，无法创建 OpenAILLM")
        return OpenAILLM(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            base_url=settings.OPENAI_BASE_URL,
        )

    if backend == "ollama":
        raise ValueError("Ollama 后端尚未实现（预留中）")

    msg = f"不支持的 LLM_BACKEND: {backend!r}，可选值: deepseek, openai, ollama"
    raise ValueError(msg)
