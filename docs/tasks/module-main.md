# M25：主入口模块 (main.py)

**阶段**: Phase 7 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M22 API Routes、M23 Container

---

## 任务清单

### 1. FastAPI 应用

- [ ] 创建 `backend/app/main.py`
  - [ ] 创建 `FastAPI` 应用实例
    - [ ] `title="MyRAG API"`
    - [ ] `version="0.1.0"`
    - [ ] `docs_url="/docs"`（Swagger UI）
  - [ ] 创建**全局 Container 实例** `_container`
  - [ ] 注册 CORS 中间件（从 settings.SERVER_CORS_ORIGINS 配置）
  - [ ] 注册全局异常处理器
    - [ ] ValueError → 400
    - [ ] HTTPException → 透传
    - [ ] 通用 Exception → 500（记录日志）
  - [ ] 包含 `api/v1/v1_router`
  - [ ] 添加健康检查接口 `GET /health`

### 2. 生命周期事件

- [ ] `@app.on_event("startup")` — 调用 `_container.initialize()`
  - [ ] 初始化数据库
  - [ ] 创建表（开发环境）
- [ ] `@app.on_event("shutdown")` — 调用 `_container.close()`
  - [ ] 关闭数据库连接

### 3. 启动脚本

- [ ] 创建 `backend/run.py`（简单入口）
  ```python
  import uvicorn
  from app.main import app

  if __name__ == "__main__":
      uvicorn.run(app, host="0.0.0.0", port=8000)
  ```

### 4. 验证

- [ ] `uvicorn app.main:app` 可正常启动
- [ ] `GET /health` 返回 200
- [ ] `GET /docs` 显示 Swagger 页面
- [ ] 启动和关闭无报错

---

## 验收标准

- [ ] FastAPI 应用正确创建
- [ ] CORS 配置可跨域
- [ ] Swagger 文档可访问
- [ ] 生命周期事件完整（startup → initialize table, shutdown → close）
- [ ] 健康检查端点可用
