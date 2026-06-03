# M07：任务队列模块 (core/task_queue)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M01 Config

**参考设计**: [详细设计文档 Module-07](../详细设计文档.md#module-07-任务队列模块-coretask_queue)

---

## 任务清单

### 1. 抽象接口

- [ ] 创建 `backend/app/core/task_queue/__init__.py`
- [ ] 创建 `backend/app/core/task_queue/base.py`
  - [ ] `TaskQueueBackend` 抽象类
  - [ ] `enqueue(task_name: str, *args, **kwargs) -> str`
  - [ ] `enqueue_with_delay(task_name: str, delay_seconds: int, *args, **kwargs) -> str`
  - [ ] `get_task_status(task_id: str) -> str` — 返回 pending/running/completed/failed
  - [ ] `get_result(task_id: str, timeout: int = 10) -> Any`
  - [ ] `register_task(name: str, fn: Callable)`

### 2. Huey + SQLite 实现

- [ ] 创建 `backend/app/core/task_queue/huey_queue.py`
  - [ ] `HueyTaskQueue(TaskQueueBackend)`
  - [ ] `__init__(db_path: str = "./data/tasks.sqlite")` — 初始化 SqliteHuey
  - [ ] `register_task()` — 使用 `@self._huey.task()` 装饰器包装
  - [ ] `enqueue()` — 调用注册的任务函数
  - [ ] `enqueue_with_delay()` — 使用 Huey 的 schedule
  - [ ] `get_task_status()` — 读取 Huey task 状态
  - [ ] `get_result()` — 获取任务返回结果

### 3. 测试

- [ ] 创建 `backend/app/core/tests/test_huey_queue.py`
  - [ ] 使用临时 SQLite 文件路径
  - [ ] 测试注册任务函数
  - [ ] 测试入队并执行成功
  - [ ] 测试延迟执行
  - [ ] 测试未注册的任务名 → 抛出 ValueError
  - [ ] 测试查询任务状态
- [ ] 创建 `backend/app/core/tests/conftest.py`（更新）
  - [ ] Fixture：`tmp_sqlite` 临时文件路径

### 4. 验证

- [ ] 任务注册 → 执行 → 获取结果 流程完整
- [ ] 队列消费者能正常处理任务
- [ ] `pytest backend/app/core/tests/test_huey_queue.py` 全部通过

---

## 验收标准

- [ ] Huey + SQLite 实现零外部依赖（不需要 Redis）
- [ ] 接口支持切换为 Celery/ARQ（接口一致）
- [ ] 任务状态可查询
- [ ] 延迟执行功能正常
