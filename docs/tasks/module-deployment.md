# D01：部署与文档模块

**阶段**: Phase 9 | **优先级**: P1 | **状态**: 🔲 未开始

**依赖模块**: 所有模块

---

## 任务清单

### 1. Docker 部署

- [ ] 完善 `backend/Dockerfile`
  - [ ] 基于 `python:3.11-slim`
  - [ ] 安装系统依赖（gcc、libglib 等）
  - [ ] 复制 requirements.txt 并 pip install
  - [ ] 复制代码
  - [ ] 启动命令
- [ ] 创建 `frontend/Dockerfile`
  - [ ] 多阶段构建（node build → nginx serve）
  - [ ] 复制 nginx 配置
- [ ] 完善 `docker-compose.yml`
  - [ ] 后端服务
  - [ ] 前端服务（nginx）
  - [ ] 数据卷（持久化 SQLite、ChromaDB、上传文件）
  - [ ] 环境变量占位
  - [ ] 网络配置

### 2. 开发环境运行文档

- [ ] README.md 补充：
  - [ ] 前置条件（Python 3.10+、Node.js 18+）
  - [ ] 快速开始（后端）
    - [ ] `cd backend`
    - [ ] `python -m venv venv`
    - [ ] `pip install -r requirements.txt`
    - [ ] 配置 `.env`
    - [ ] `python run.py`
  - [ ] 快速开始（前端）
    - [ ] `cd frontend`
    - [ ] `npm install`
    - [ ] `npm run dev`
  - [ ] Docker 部署
    - [ ] `docker-compose up -d`

### 3. 配置说明

- [ ] `.env.example` 完善注释
- [ ] `config.yaml` 完整配置注释

### 4. API 文档

- [ ] 确保 FastAPI Swagger 文档完整
- [ ] API 接口有 summary 和 description 注释

### 5. 验证

- [ ] 本地开发可正常启动
- [ ] Docker 部署可正常启动
- [ ] 前端可正常连接后端

---

## 验收标准

- [ ] `docker-compose up` 一键启动全套服务
- [ ] 本地开发环境 5 分钟内可跑起来
- [ ] README 完整覆盖前置条件、安装、配置、运行步骤
