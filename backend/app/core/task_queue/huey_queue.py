"""Huey + SQLite 任务队列实现 — HueyTaskQueue

基于 SqliteHuey，零外部依赖（不需要 Redis）。
支持 immediate 模式（同步执行，适合测试）和消费者模式（独立进程执行，适合生产）。

用法::

    # 测试模式 — 立即同步执行
    queue = HueyTaskQueue(db_path=\":memory:\", immediate=True)
    queue.register_task(\"add\", lambda a, b: a + b)
    task_id = queue.enqueue(\"add\", 1, 2)
    assert queue.get_result(task_id) == 3

    # 生产模式 — 需单独启动消费者
    queue = HueyTaskQueue(db_path=\"./data/tasks.sqlite\")
    queue.register_task(\"send_email\", send_email)
    queue.enqueue(\"send_email\", \"alice@example.com\", \"Hello!\")
"""

import os
from typing import Any, Callable, Dict

from huey import Error, SqliteHuey
from huey.api import Result
from huey.constants import EmptyData
from huey.serializer import Serializer

from app.core.exceptions import TaskQueueError
from app.core.task_queue.base import TaskQueueBackend


class HueyTaskQueue(TaskQueueBackend):
    """基于 Huey + SQLite 的任务队列实现

    通过 SqliteHuey 使用 SQLite 作为任务存储后端，支持即时执行
    （immediate 模式）和异步消费者执行两种模式。

    属性:
        huey: 底层 SqliteHuey 实例，可直接访问 Huey 的完整 API
    """

    def __init__(
        self,
        db_path: str = "./data/tasks.sqlite",
        immediate: bool = False,
    ) -> None:
        """初始化 Huey 任务队列

        参数:
            db_path:   SQLite 数据库文件路径。
                      传入 ``\":memory:\"`` 使用内存数据库（仅测试用）。
            immediate: 若为 True，入队时立即同步执行（适合测试和开发）；
                      若为 False，需要独立消费者进程执行任务（适合生产）。

        异常:
            TaskQueueError: 数据库文件所在目录创建失败时抛出
        """
        # 仅在非 ":memory:" 模式下创建目录
        if db_path != ":memory:":
            db_dir = os.path.dirname(db_path)
            if db_dir:
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except OSError as exc:
                    raise TaskQueueError(
                        message=f"无法创建任务队列数据库目录: {db_dir}",
                        detail=str(exc),
                    ) from exc

        self._huey: SqliteHuey = SqliteHuey(
            name="rag_task_queue",
            filename=db_path,
            immediate=immediate,
            # store_none=True 确保返回 None 的任务也在结果存储中留下记录，
            # 便于区分“已执行返回 None”和“未执行”
            store_none=True,
        )
        self._registry: Dict[str, Any] = {}

    @property
    def huey(self) -> SqliteHuey:
        """底层 SqliteHuey 实例"""
        return self._huey

    # ── 接口实现 ──────────────────────────────────────────────

    def register_task(self, name: str, fn: Callable) -> None:
        """注册任务函数

        使用 Huey 的 ``task()`` 装饰器包装函数，使其可被队列调度。
        同名任务不可重复注册。

        异常:
            TaskQueueError: 同名任务已注册时抛出
        """
        if name in self._registry:
            raise TaskQueueError(
                message=f"任务已注册: {name}",
                detail="请使用不同的名称注册，或先注销原任务",
            )

        wrapper = self._huey.task(name=name)(fn)
        self._registry[name] = wrapper

    def enqueue(self, task_name: str, *args: Any, **kwargs: Any) -> str:
        """将任务加入队列

        查找已注册的任务包装器，调用它以创建 Task 并调用 Huey 入队。
        返回 Huey 生成的唯一任务 ID。

        异常:
            ValueError: task_name 未注册时抛出
        """
        wrapper = self._get_wrapper(task_name)
        result: Result = wrapper(*args, **kwargs)
        return result.id

    def enqueue_with_delay(
        self, task_name: str, delay_seconds: int, *args: Any, **kwargs: Any
    ) -> str:
        """延迟 ``delay_seconds`` 秒后执行任务

        使用 Huey 的 ``schedule()`` 方法设置 ``eta``（期望执行时间）。
        消费者将在到达 eta 后执行该任务。

        在 ``immediate=True`` 模式下，若 delay_seconds > 0，任务会被
        加入调度表（而非立即执行），需等待消费者或调用 run_schedule() 执行。
        delay_seconds=0 等同于立即执行。

        异常:
            ValueError: task_name 未注册时抛出
        """
        wrapper = self._get_wrapper(task_name)
        result: Result = wrapper.schedule(
            args=args,
            kwargs=kwargs,
            delay=delay_seconds,
        )
        return result.id

    def get_task_status(self, task_id: str) -> str:
        """查询任务执行状态

        通过检查 Huey 结果存储中的记录判断状态：
        - 无记录 → ``\"pending\"``（等待执行或正在执行）
        - 有记录且值为 ``Error`` 类型 → ``\"failed\"``
        - 有记录且值为普通类型 → ``\"completed\"``
        """
        raw = self._huey.get_raw(task_id, peek=True)
        if raw is EmptyData:
            return "pending"

        data = self._huey.serializer.deserialize(raw)
        if isinstance(data, Error):
            return "failed"
        return "completed"

    def get_result(self, task_id: str, timeout: int = 10) -> Any:
        """获取任务执行结果

        使用 ``huey.result()`` 方法获取结果。
        timeout > 0 时阻塞等待结果就绪；timeout = 0 时不等待，结果尚未
        就绪时返回 ``None``。

        返回:
            任务函数的返回值

        异常:
            TaskQueueError: 任务执行失败时抛出，detail 包含原始异常信息
        """
        blocking = timeout > 0
        try:
            return self._huey.result(
                task_id,
                blocking=blocking,
                timeout=timeout if blocking else None,
            )
        except Exception as exc:
            raise TaskQueueError(
                message=f"任务执行失败: {task_id}",
                detail=str(exc),
            ) from exc

    # ── 私有辅助 ──────────────────────────────────────────────

    def _get_wrapper(self, task_name: str) -> Any:
        """按名称查找已注册的任务包装器

        返回:
            TaskWrapper 实例

        异常:
            ValueError: 任务未注册时抛出，附带已注册的任务列表
        """
        wrapper = self._registry.get(task_name)
        if wrapper is None:
            registered = list(self._registry.keys())
            raise ValueError(
                f"任务未注册: {task_name!r}。已注册的任务: {registered}"
            )
        return wrapper
