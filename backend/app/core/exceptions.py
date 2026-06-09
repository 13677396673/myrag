"""全局异常定义

所有业务异常的基类 `RagError`，统一携带 code、message、detail 三个字段。
其他模块的异常应继承此基类。
"""

from typing import Any, Optional


class RagError(Exception):
    """所有应用异常的基类

    属性:
        code: 机器可读的错误码（如 ``config_invalid``）
        message: 人类可读的简短描述
        detail: 可选详细信息或上下文
    """

    def __init__(
        self,
        code: str = "internal_error",
        message: str = "An internal error occurred",
        detail: Optional[Any] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        if self.detail:
            parts.append(f" — {self.detail}")
        return "".join(parts)


class ConfigError(RagError):
    """配置相关错误"""

    def __init__(
        self,
        message: str = "Configuration error",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(code="config_error", message=message, detail=detail)


class StorageError(RagError):
    """存储相关错误"""

    def __init__(
        self,
        message: str = "Storage error",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(code="storage_error", message=message, detail=detail)


class DatabaseError(RagError):
    """数据库相关错误"""

    def __init__(
        self,
        message: str = "Database error",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(code="database_error", message=message, detail=detail)


class TaskQueueError(RagError):
    """任务队列相关错误"""

    def __init__(
        self,
        message: str = "Task queue error",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(code="task_queue_error", message=message, detail=detail)
