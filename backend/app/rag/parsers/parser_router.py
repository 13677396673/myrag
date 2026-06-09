"""解析器路由 — ParserRouter

动态注册和路由文档解析器，根据文件扩展名自动选择对应的解析器实例。

用法::

    router = ParserRouter()
    router.register(TextParser)
    parser = router.get_parser(".txt")
    doc = parser.parse("/path/to/file.txt")
"""

from typing import Dict, List, Optional, Type

from app.rag.interfaces.parser import DocumentParser


class ParserRouter:
    """文档解析器路由

    维护 ``{扩展名 → 解析器类}`` 的映射表，支持运行时动态注册和查询。

    属性:
        _registry: ``{".ext": Type[DocumentParser]}`` 映射
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Type[DocumentParser]] = {}

    def register(self, parser_cls: Type[DocumentParser]) -> None:
        """注册一个解析器

        将 ``parser_cls.supported_extensions()`` 返回的全部扩展名映射到
        该解析器类。如果扩展名已被注册，会被新注册覆盖。

        参数:
            parser_cls: 继承自 ``DocumentParser`` 的解析器类

        异常:
            TypeError: 如果 ``parser_cls`` 不是 ``DocumentParser`` 的子类
        """
        # 必须传入类（而非实例）
        if not isinstance(parser_cls, type):
            raise TypeError(
                f"{type(parser_cls).__name__} 不是 DocumentParser 的子类"
            )
        if not issubclass(parser_cls, DocumentParser):
            raise TypeError(
                f"{parser_cls.__name__} 不是 DocumentParser 的子类"
            )

        for ext in parser_cls.supported_extensions():
            self._registry[ext] = parser_cls

    def get_parser(self, extension: str) -> Optional[DocumentParser]:
        """根据扩展名获取解析器实例

        参数:
            extension: 文件扩展名，如 ``".txt"``、``".pdf"``

        返回:
            - 找到 → 解析器实例
            - 未注册 → ``None``
        """
        ext = extension.lower()
        parser_cls = self._registry.get(ext)
        if parser_cls is None:
            return None
        return parser_cls()

    def get_supported_extensions(self) -> List[str]:
        """列出所有已注册的扩展名

        返回:
            已排序的扩展名字符串列表
        """
        return sorted(self._registry.keys())
