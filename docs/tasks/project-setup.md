# M00：项目骨架搭建

**阶段**: Phase 0 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: 无（这是第一个任务）

---

## 任务清单

### 1. 项目目录结构创建

- [x] 在 `D:\claudeproject\myrag\` 下创建后端目录结构
  - [x] `backend/app/` — 应用主包
  - [x] `backend/app/config/`
  - [x] `backend/app/models/`
  - [x] `backend/app/schemas/`
  - [x] `backend/app/api/v1/`
  - [x] `backend/app/services/`
  - [x] `backend/app/rag/interfaces/`
  - [x] `backend/app/rag/parsers/`
  - [x] `backend/app/rag/splitters/`
  - [x] `backend/app/rag/embeddings/`
  - [x] `backend/app/rag/vector_stores/`
  - [x] `backend/app/rag/llms/`
  - [x] `backend/app/rag/retrievers/`
  - [x] `backend/app/core/`
  - [x] `backend/app/core/storage/`
  - [x] `backend/app/core/task_queue/`
  - [x] `backend/app/tasks/`
  - [x] `backend/tests/`
  - [x] `backend/data/` — 运行时数据目录
- [x] 在每个 Python 子包下创建 `__init__.py`
- [x] 在 `backend/app/` 下创建 `__init__.py`

### 2. 依赖管理

- [x] 创建 `backend/requirements.txt`
  - `fastapi`
  - `uvicorn[standard]`
  - `sqlalchemy[asyncio]`
  - `aiosqlite`
  - `pydantic-settings`
  - `python-dotenv`
  - `python-jose[cryptography]` (JWT)
  - `bcrypt`
  - `httpx`
  - `aiofiles`
  - `openai`
  - `sentence-transformers`
  - `chromadb`
  - `PyMuPDF`
  - `python-docx`
  - `huey`
  - `python-multipart`
- [ ] 创建 `backend/requirements-dev.txt`
  - `pytest`
  - `pytest-asyncio`
  - `pytest-cov`
  - `httpx` (for TestClient)
  - `pytest-httpx`
- [x] 创建 `backend/requirements-dev.txt`

### 3. 基础配置文件

- [x] 创建 `.env.example`（不含真实密钥的模板）
- [x] 创建 `.gitignore`
  - Python 缓存 (`__pycache__/`, `*.pyc`)
  - 环境变量 (`.env`)
  - 运行时数据 (`backend/data/`)
  - 虚拟环境 (`venv/`, `.venv/`)
  - IDE 配置 (`.vscode/`, `.idea/`)
  - Node 模块 (`frontend/node_modules/`)
- [x] 创建 `backend/Dockerfile`（骨架，后续完善）
- [x] 创建 `docker-compose.yml`（骨架，后续完善）

### 4. README

- [x] 创建 `README.md`
  - 项目简介
  - 核心功能列表
  - 技术栈概览
  - 快速开始指引

### 5. 验证

- [x] 项目结构符合 [概要设计文档](../概要设计文档.md#十项目目录结构)
- [x] 每个子包有 `__init__.py`
- [x] `pip install -r requirements.txt` 可成功安装
- [x] `.gitignore` 覆盖了所有不应提交的文件类型

---

## 测试策略

此模块为纯文件创建，无 Python 代码可测试。

## 验收标准

- [x] `git init` 后 `git status` 显示正确的文件列表
- [x] 依赖安装无报错
- [x] 目录结构满足后续开发需求
