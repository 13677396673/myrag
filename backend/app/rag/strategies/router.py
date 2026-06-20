"""StrategyRouter — 文档 chunking 策略路由

根据文件扩展名选择对应的 ChunkingStrategy。
"""

from typing import Dict, List, Optional

from .base import ChunkingStrategy


class StrategyRouter:
    """文档 chunking 策略路由

    将文件扩展名映射到 (parser, splitter) 配对策略。

    与 ``ParserRouter`` 的关系：
    - ``ParserRouter`` 只负责解析，将扩展名 → 解析器
    - ``StrategyRouter`` 负责完整策略，将扩展名 → (解析器, 切片器) 配对
    - StrategyRouter 取代了 Pipeline 中同时持有 ParserRouter + Splitter 的方式
    """

    def __init__(self):
        self._strategies: Dict[str, ChunkingStrategy] = {}

    def register(
        self,
        extensions: List[str],
        strategy: ChunkingStrategy,
    ) -> None:
        """注册一个策略到多个扩展名

        参数:
            extensions: 文件扩展名列表，如 ``[".md", ".markdown"]``
            strategy: ChunkingStrategy 实例
        """
        for ext in extensions:
            self._strategies[ext.lower()] = strategy

    def get_strategy(self, ext: str) -> Optional[ChunkingStrategy]:
        """获取指定扩展名对应的策略

        参数:
            ext: 文件扩展名，如 ``".pdf"``、``".md"``

        返回:
            匹配的 ChunkingStrategy，或 None（无匹配的策略）
        """
        return self._strategies.get(ext.lower())

    def get_supported_extensions(self) -> List[str]:
        """返回所有已注册的扩展名列表"""
        return list(self._strategies.keys())

    def get_all_strategies(self) -> List[ChunkingStrategy]:
        """返回所有已注册的策略（去重）"""
        seen = set()
        result = []
        for strategy in self._strategies.values():
            if id(strategy) not in seen:
                seen.add(id(strategy))
                result.append(strategy)
        return result
