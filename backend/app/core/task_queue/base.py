"""任务队列抽象接口 — TaskQueueBackend

定义任务队列后端的统一抽象，所有具体实现（Huey+SQLite、Celery、ARQ）必须
继承此基类并实现所有方法。

用法::

    class MyQueue(TaskQueueBackend):
        def register_task(self, name, fn): ...
        def enqueue(self, task_name, *args, **kwargs) -> str: ...
        def enqueue_with_delay(self, task_name, delay_seconds, *args, **kwargs) -> str: ...
        def get_task_status(self, task_id) -> str: ...
        def get_result(self, task_id, timeout=10) -> Any: ...
"""

from abc import ABC, abstractmethod
from typing import Any, Callable


class TaskQueueBackend(ABC):
    """任务队列后端抽象接口

    支持注册任务函数、入队执行、延迟执行、状态查询和结果获取。
    接口设计为同步（因为当前实现 Huey/SQLite 为同步操作），
    如需异步后端可继承此类并覆盖为 async 方法。

    所有方法均使用字符串 ``task_id`` 标识任务实例，使用字符串 ``task_name``
    标识已注册的任务类型。
    """

    @abstractmethod
    def register_task(self, name: str, fn: Callable) -> None:
        """注册一个可执行的任务函数

        参数:
            name: 任务名称，用于后续 ``enqueue()`` 引用
            fn:   任务函数

        异常:
            TaskQueueError: 同名任务已注册时抛出
        """
        ...

    @abstractmethod
    def enqueue(self, task_name: str, *args: Any, **kwargs: Any) -> str:
        """将任务加入队列并立即返回任务 ID

        参数:
            task_name: 已注册的任务名称
            *args:     传递给任务函数的位置参数
            **kwargs:  传递给任务函数的关键字参数

        返回:
            唯一任务 ID（字符串）

        异常:
            ValueError: task_name 未注册时抛出
        """
        ...

    @abstractmethod
    def enqueue_with_delay(
        self, task_name: str, delay_seconds: int, *args: Any, **kwargs: Any
    ) -> str:
        """延迟 ``delay_seconds`` 秒后执行任务

        参数:
            task_name:     已注册的任务名称
            delay_seconds: 延迟秒数（必须 >= 0）
            *args:         传递给任务函数的位置参数
            **kwargs:      传递给任务函数的关键字参数

        返回:
            唯一任务 ID（字符串）

        异常:
            ValueError: task_name 未注册时抛出
        """
        ...

    @abstractmethod
    def get_task_status(self, task_id: str) -> str:
        """查询任务执行状态

        参数:
            task_id: 任务 ID

        返回:
            - ``"pending"``   — 等待执行或正在执行
            - ``"completed"`` — 执行成功
            - ``"failed"``    — 执行失败（抛出异常）
        """
        ...

    @abstractmethod
    def get_result(self, task_id: str, timeout: int = 10) -> Any:
        """获取任务执行结果

        参数:
            task_id: 任务 ID
            timeout: 等待秒数。
                     0 表示不等待，结果尚未就绪时返回 ``None``；
                     > 0 表示阻塞等待最多 timeout 秒。

        返回:
            任务函数的返回值；若结果尚未就绪且 timeout=0 则返回 ``None``

        异常:
            TaskQueueError: 任务执行失败时抛出，detail 包含原始异常信息
        """
        ...
