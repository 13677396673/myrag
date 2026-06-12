# M25：主入口模块 (main.py)

**阶段**: Phase 7 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M22 API Routes、M23 Container

---

## 任务清单

### 1. FastAPI 应用

- [x] 创建 `backend/app/main.py`
  - [x] 创建 `FastAPI` 应用实例
    - [x] `title="MyRAG API"`
    - [x] `version="0.1.0"`
    - [x] `docs_url="/docs"`（Swagger UI）
  - [x] 创建**全局 Container 实例** `_container`
  - [x] 注册 CORS 中间件（从 settings.SERVER_CORS_ORIGINS 配置）
  - [x] 注册全局异常处理器
    - [x] ValueError → 400
    - [x] HTTPException → 透传
    - [x] 通用 Exception → 500（记录日志）
  - [x] 包含 `api/v1/v1_router`
  - [x] 添加健康检查接口 `GET /health`

### 2. 生命周期事件

- [x] `@app.on_event("startup")` — 调用 `_container.initialize()`
  - [x] 初始化数据库
  - [x] 创建表（开发环境）
- [x] `@app.on_event("shutdown")` — 调用 `_container.close()`
  - [x] 关闭数据库连接

### 3. 启动脚本

- [x] 创建 `backend/run.py`（简单入口）

### 4. 验证

- [x] `uvicorn app.main:app` 可正常启动
- [x] `GET /health` 返回 200
- [x] `GET /docs` 显示 Swagger 页面
- [x] 启动和关闭无报错

---

## 验收标准

- [x] FastAPI 应用正确创建
- [x] CORS 配置可跨域
- [x] Swagger 文档可访问
- [x] 生命周期事件完整（startup → initialize table, shutdown → close）
- [x] 健康检查端点可用
