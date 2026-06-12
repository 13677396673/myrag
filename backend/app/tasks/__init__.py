"""异步任务定义模块

集中定义所有可由 ``TaskQueueBackend`` 调度的异步业务任务。
当前只包含文档处理任务，后续可扩展为数据集处理、清理任务等。

用法::

    from app.tasks import register_tasks

    register_tasks(task_queue)
    task_queue.enqueue("process_document", "doc-001")
"""

from .document_tasks import process_document, register_tasks

__all__ = [
    "process_document",
    "register_tasks",
]
