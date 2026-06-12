# D01：部署与文档模块

**阶段**: Phase 9 | **优先级**: P1 | **状态**: ✅ 已完成

**依赖模块**: 所有模块

---

## 任务清单

### 1. Docker 部署

- [x] 完善 `backend/Dockerfile`
  - [x] 基于 `python:3.11-slim`
  - [x] 安装系统依赖（gcc、libglib 等）
  - [x] 复制 requirements.txt 并 pip install
  - [x] 复制代码
  - [x] 启动命令
- [x] 创建 `frontend/Dockerfile`
  - [x] 多阶段构建（node build → nginx serve）
  - [x] 复制 nginx 配置
- [x] 完善 `docker-compose.yml`
  - [x] 后端服务
  - [x] 前端服务（nginx）
  - [x] 数据卷（持久化 SQLite、ChromaDB、上传文件）
  - [x] 环境变量占位
  - [x] 网络配置

### 2. 开发环境运行文档

- [x] README.md 补充：
  - [x] 前置条件（Python 3.10+、Node.js 18+）
  - [x] 快速开始（后端）
    - [x] `cd backend`
    - [x] `python -m venv venv`
    - [x] `pip install -r requirements.txt`
    - [x] 配置 `.env`
    - [x] `python run.py`
  - [x] 快速开始（前端）
    - [x] `cd frontend`
    - [x] `npm install`
    - [x] `npm run dev`
  - [x] Docker 部署
    - [x] `docker-compose up -d`

### 3. 配置说明

- [x] `.env.example` 完善注释
- [x] `config.yaml` 完整配置注释

### 4. API 文档

- [x] 确保 FastAPI Swagger 文档完整
- [x] API 接口有 summary 和 description 注释

### 5. 验证

- [x] 本地开发可正常启动
- [x] Docker 部署可正常启动
- [x] 前端可正常连接后端

---

## 验收标准

- [x] `docker-compose up` 一键启动全套服务
- [x] 本地开发环境 5 分钟内可跑起来
- [x] README 完整覆盖前置条件、安装、配置、运行步骤
