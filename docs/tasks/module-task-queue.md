# M07：任务队列模块 (core/task_queue)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M01 Config

**参考设计**: [详细设计文档 Module-07](../详细设计文档.md#module-07-任务队列模块-coretask_queue)

---

## 任务清单

### 1. 抽象接口

- [x] 创建 `backend/app/core/task_queue/__init__.py`
- [x] 创建 `backend/app/core/task_queue/base.py`
  - [x] `TaskQueueBackend` 抽象类
  - [x] `enqueue(task_name: str, *args, **kwargs) -> str`
  - [x] `enqueue_with_delay(task_name: str, delay_seconds: int, *args, **kwargs) -> str`
  - [x] `get_task_status(task_id: str) -> str` — 返回 pending/running/completed/failed
  - [x] `get_result(task_id: str, timeout: int = 10) -> Any`
  - [x] `register_task(name: str, fn: Callable)`

### 2. Huey + SQLite 实现

- [x] 创建 `backend/app/core/task_queue/huey_queue.py`
  - [x] `HueyTaskQueue(TaskQueueBackend)`
  - [x] `__init__(db_path: str = "./data/tasks.sqlite")` — 初始化 SqliteHuey
  - [x] `register_task()` — 使用 `@self._huey.task()` 装饰器包装
  - [x] `enqueue()` — 调用注册的任务函数
  - [x] `enqueue_with_delay()` — 使用 Huey 的 schedule
  - [x] `get_task_status()` — 读取 Huey task 状态
  - [x] `get_result()` — 获取任务返回结果

### 3. 测试

- [x] 创建 `backend/app/core/tests/test_huey_queue.py`
  - [x] 使用临时 SQLite 文件路径
  - [x] 测试注册任务函数
  - [x] 测试入队并执行成功
  - [x] 测试延迟执行
  - [x] 测试未注册的任务名 → 抛出 ValueError
  - [x] 测试查询任务状态
- [x] 创建 `backend/app/core/tests/conftest.py`（更新）
  - [x] Fixture：`tmp_sqlite` 临时文件路径

### 4. 验证

- [x] 任务注册 → 执行 → 获取结果 流程完整
- [x] 队列消费者能正常处理任务
- [x] `pytest backend/app/core/tests/test_huey_queue.py` 全部通过

---

## 验收标准

- [x] Huey + SQLite 实现零外部依赖（不需要 Redis）
- [x] 接口支持切换为 Celery/ARQ（接口一致）
- [x] 任务状态可查询
- [x] 延迟执行功能正常
- [x] 21 个测试用例全部通过，零回归
