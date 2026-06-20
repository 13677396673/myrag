"""文档 chunking 策略模块

提供 ``ChunkingStrategy`` 数据类和 ``StrategyRouter`` 路由，
将文档类型映射到 (parser, splitter) 配对，实现按文档类型的结构化切分。

用法::

    from app.rag.strategies import StrategyRouter, ChunkingStrategy

    router = StrategyRouter()
    router.register([".md", ".markdown"], markdown_parser, markdown_splitter)
    strategy = router.get_strategy(".md")
    # strategy.parser → markdown_parser
    # strategy.splitter → markdown_splitter
"""

from .base import ChunkingStrategy
from .router import StrategyRouter
from .defaults import register_default_strategies

__all__ = [
    "ChunkingStrategy",
    "StrategyRouter",
    "register_default_strategies",
]
