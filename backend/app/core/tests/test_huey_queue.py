"""HueyTaskQueue 任务队列实现测试

测试覆盖：
- 任务注册与未注册异常
- 入队执行与结果获取
- 延迟执行
- 任务状态查询（pending / completed / failed）
- 重复注册检查
- 内存数据库支持
- 自定义 db_path 目录自动创建
"""

import os
import tempfile

import pytest

from app.core.exceptions import TaskQueueError
from app.core.task_queue import HueyTaskQueue


# ── 辅助任务函数 ────────────────────────────────────────────


def add(a: int, b: int) -> int:
    """简单的加法任务"""
    return a + b


def multiply(a: int, b: int) -> int:
    """乘法任务"""
    return a * b


def failing_task(_msg: str = "") -> None:
    """总是失败的任务"""
    raise ValueError("任务执行失败")


def returns_none() -> None:
    """返回 None 的任务"""
    return None


class TestHueyTaskQueue:
    """HueyTaskQueue 功能测试"""

    # ── 任务注册 ────────────────────────────────────────────

    def test_register_task(self, huey_task_queue: HueyTaskQueue) -> None:
        """注册任务后，内部 registry 包含该任务"""
        huey_task_queue.register_task("add", add)
        assert "add" in huey_task_queue._registry

    def test_register_duplicate_task(self, huey_task_queue: HueyTaskQueue) -> None:
        """注册同名任务应抛出 TaskQueueError"""
        huey_task_queue.register_task("add", add)
        with pytest.raises(TaskQueueError, match="任务已注册"):
            huey_task_queue.register_task("add", multiply)

    # ── 入队与执行 ──────────────────────────────────────────

    def test_enqueue_and_get_result(self, huey_task_queue: HueyTaskQueue) -> None:
        """入队任务后，能获取正确的返回值"""
        huey_task_queue.register_task("add", add)
        task_id = huey_task_queue.enqueue("add", 1, 2)
        assert isinstance(task_id, str)
        assert len(task_id) > 0

        result = huey_task_queue.get_result(task_id, timeout=5)
        assert result == 3

    def test_enqueue_unregistered_task(self, huey_task_queue: HueyTaskQueue) -> None:
        """未注册的任务名应抛出 ValueError"""
        with pytest.raises(ValueError, match="任务未注册"):
            huey_task_queue.enqueue("nonexistent", 1, 2)

    def test_multiple_tasks(self, huey_task_queue: HueyTaskQueue) -> None:
        """多次入队不同任务，各结果正确"""
        huey_task_queue.register_task("add", add)
        huey_task_queue.register_task("multiply", multiply)

        id1 = huey_task_queue.enqueue("add", 10, 20)
        id2 = huey_task_queue.enqueue("multiply", 6, 7)

        assert huey_task_queue.get_result(id1) == 30
        assert huey_task_queue.get_result(id2) == 42

    # ── 延迟执行 ────────────────────────────────────────────

    def test_enqueue_with_delay_zero(self, huey_task_queue: HueyTaskQueue) -> None:
        """delay=0 等同于立即执行"""
        huey_task_queue.register_task("add", add)
        task_id = huey_task_queue.enqueue_with_delay("add", 0, 3, 4)
        assert isinstance(task_id, str)

        result = huey_task_queue.get_result(task_id, timeout=5)
        assert result == 7

    def test_enqueue_with_delay_future(self, huey_task_queue: HueyTaskQueue) -> None:
        """delay > 0 的任务被加入调度表，状态为 pending"""
        huey_task_queue.register_task("add", add)
        task_id = huey_task_queue.enqueue_with_delay("add", 3600, 5, 5)
        assert isinstance(task_id, str)

        # 在 immediate 模式下，延迟 > 0 的任务不会被立即执行
        status = huey_task_queue.get_task_status(task_id)
        assert status == "pending"

    def test_enqueue_with_delay_unregistered(self, huey_task_queue: HueyTaskQueue) -> None:
        """延迟执行未注册任务应抛出 ValueError"""
        with pytest.raises(ValueError, match="任务未注册"):
            huey_task_queue.enqueue_with_delay("nonexistent", 10, 1, 2)

    # ── 状态查询 ────────────────────────────────────────────

    def test_status_completed(self, huey_task_queue: HueyTaskQueue) -> None:
        """执行成功的任务状态为 completed"""
        huey_task_queue.register_task("add", add)
        task_id = huey_task_queue.enqueue("add", 1, 1)
        status = huey_task_queue.get_task_status(task_id)
        assert status == "completed"

    def test_status_failed(self, huey_task_queue: HueyTaskQueue) -> None:
        """执行失败的任务状态为 failed"""
        huey_task_queue.register_task("fail", failing_task)
        task_id = huey_task_queue.enqueue("fail", "oops")
        status = huey_task_queue.get_task_status(task_id)
        assert status == "failed"

    def test_status_pending_for_scheduled(self, huey_task_queue: HueyTaskQueue) -> None:
        """延迟 > 0 且未执行的任务状态为 pending"""
        huey_task_queue.register_task("add", add)
        task_id = huey_task_queue.enqueue_with_delay("add", 86400, 1, 2)
        assert huey_task_queue.get_task_status(task_id) == "pending"

    def test_status_nonexistent_task_id(self, huey_task_queue: HueyTaskQueue) -> None:
        """不存在的任务 ID 应返回 pending（表示无法确定状态）"""
        status = huey_task_queue.get_task_status("non_existent_id_12345")
        assert status == "pending"

    # ── 结果获取 ────────────────────────────────────────────

    def test_get_result_blocking(self, huey_task_queue: HueyTaskQueue) -> None:
        """阻塞等待结果，能获取返回值"""
        huey_task_queue.register_task("add", add)
        task_id = huey_task_queue.enqueue("add", 100, 200)
        result = huey_task_queue.get_result(task_id, timeout=5)
        assert result == 300

    def test_get_result_timeout_zero(self, huey_task_queue: HueyTaskQueue) -> None:
        """timeout=0 时，对已完成任务仍可获取结果"""
        huey_task_queue.register_task("add", add)
        task_id = huey_task_queue.enqueue("add", 2, 3)
        # Immediate 模式下，任务已执行完毕
        result = huey_task_queue.get_result(task_id, timeout=0)
        assert result == 5

    def test_get_result_failed_task(self, huey_task_queue: HueyTaskQueue) -> None:
        """获取失败任务的结果应抛出 TaskQueueError"""
        huey_task_queue.register_task("fail", failing_task)
        task_id = huey_task_queue.enqueue("fail", "bad")
        with pytest.raises(TaskQueueError, match="任务执行失败"):
            huey_task_queue.get_result(task_id, timeout=5)

    def test_get_result_none_return(self, huey_task_queue: HueyTaskQueue) -> None:
        """返回 None 的任务也能正常获取结果"""
        huey_task_queue.register_task("none", returns_none)
        task_id = huey_task_queue.enqueue("none")
        result = huey_task_queue.get_result(task_id, timeout=5)
        assert result is None

    # ── 边界情况 ────────────────────────────────────────────

    def test_immediate_mode_execution(self) -> None:
        """内存数据库 + immediate 模式能正常工作"""
        queue = HueyTaskQueue(db_path=":memory:", immediate=True)
        queue.register_task("add", add)
        task_id = queue.enqueue("add", 7, 8)
        assert queue.get_result(task_id) == 15

    def test_non_immediate_mode_queues_only(self) -> None:
        """非 immediate 模式：任务入队但不执行"""
        tmp = tempfile.mkstemp(suffix=".db", prefix="rag_nonimm_")
        os.close(tmp[0])

        queue = HueyTaskQueue(db_path=tmp[1], immediate=False)
        queue.register_task("add", add)
        task_id = queue.enqueue("add", 9, 9)

        # 非 immediate 模式，任务未执行，状态应该是 pending
        status = queue.get_task_status(task_id)
        assert status == "pending"

        try:
            os.unlink(tmp[1])
        except OSError:
            pass

    def test_custom_db_path_creates_directory(self) -> None:
        """自定义 db_path 时，目录自动创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "sub", "nested", "tasks.db")
            queue = HueyTaskQueue(db_path=db_path, immediate=True)
            assert os.path.isdir(os.path.dirname(db_path))

            queue.register_task("add", add)
            task_id = queue.enqueue("add", 1, 2)
            assert queue.get_result(task_id) == 3

    # ── 带关键字参数的任务 ──────────────────────────────────

    def test_task_with_kwargs(self, huey_task_queue: HueyTaskQueue) -> None:
        """任务函数可接受关键字参数"""

        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        huey_task_queue.register_task("greet", greet)
        task_id = huey_task_queue.enqueue("greet", "World", greeting="Hi")
        result = huey_task_queue.get_result(task_id, timeout=5)
        assert result == "Hi, World!"

    # ── 多次操作 ────────────────────────────────────────────

    def test_multiple_enqueues_same_task(self, huey_task_queue: HueyTaskQueue) -> None:
        """同一任务可多次入队，各次互不干扰"""
        huey_task_queue.register_task("add", add)
        ids = []
        for i in range(5):
            tid = huey_task_queue.enqueue("add", i, i * 2)
            ids.append(tid)

        for i, tid in enumerate(ids):
            result = huey_task_queue.get_result(tid, timeout=5)
            assert result == i + i * 2  # i + 2i = 3i
