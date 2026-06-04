"""配置管理模块 — 集中管理所有应用配置

提供全局单例 `settings`，所有模块通过
``from app.config import settings`` 访问配置。

配置加载优先级（高 → 低）:
  1. 环境变量（支持嵌套语法，如 LLM__BACKEND=openai）
  2. .env 文件
  3. config.yaml 文件
  4. Settings 类中的默认值
"""

from .settings import Settings, settings

__all__ = [
    "Settings",
    "settings",
]
