# MyRAG — 智能知识库系统

基于 **RAG（Retrieval-Augmented Generation）** 架构的智能知识库问答系统。

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 功能概览

| 功能 | 说明 |
|------|------|
| **文档管理** | 支持 PDF、DOCX、TXT、MD、CSV、JSON、HTML 等多种格式上传与解析 |
| **智能切片** | 固定大小、Markdown 结构、语义分割三种切片策略 |
| **向量检索** | BGE / OpenAI / DeepSeek Embedding + ChromaDB / FAISS / Milvus / PGVector |
| **智能问答** | 对接 DeepSeek / OpenAI / Ollama，基于知识库精准回答并标注来源 |
| **数据集管理** | 知识库按数据集灵活组织，每个数据集独立管理文档 |
| **对话管理** | 多轮对话，流式 SSE 输出，打字机效果 |
| **用户系统** | 注册登录、JWT 鉴权、角色权限（普通用户 / 管理员） |
| **管理后台** | 用户管理、系统统计 |

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | React 18 + TypeScript + Vite + Ant Design + Zustand |
| **后端** | Python FastAPI + SQLAlchemy (async) + Pydantic |
| **数据库** | SQLite（开发）/ PostgreSQL（生产） |
| **向量数据库** | ChromaDB（默认）/ FAISS / Milvus / PGVector |
| **LLM** | DeepSeek / OpenAI / Ollama |
| **Embedding** | BGE-small-zh / OpenAI / DeepSeek |
| **任务队列** | Huey（默认）/ Celery / ARQ |
| **文件存储** | LocalFS（默认）/ MinIO / S3 |
| **部署** | Docker / Docker Compose / Nginx |

---

## 快速开始（本地开发）

### 前置条件

- Python 3.11+
- Node.js 18+
- npm 9+

### 1. 克隆项目

```bash
git clone <repo-url>
cd myrag
```

### 2. 后端设置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate        # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt   # 开发环境（热重载、测试工具等）
```

### 3. 配置环境变量

```bash
# 回到项目根目录
cd ..

# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入必要的密钥（至少需要 DEEPSEEK_API_KEY）
```

### 4. 启动后端服务

```bash
cd backend
python run.py
# 或直接使用 uvicorn：
# uvicorn app.main:app --reload --port 8000
```

启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 5. 启动前端开发服务器

```bash
# 新开一个终端
cd frontend
npm install
npm run dev
```

前端默认运行在 http://localhost:3000，自动代理 API 请求到后端 8000 端口。

---

## Docker 一键部署

### 前置条件

- Docker Engine 24+
- Docker Compose v2+

### 启动全部服务

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入密钥

# 2. 一键启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

### 访问服务

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |

### 数据持久化

Docker 部署时使用命名卷 `myrag-data` 持久化以下数据：
- `data/myrag.db` — SQLite 数据库
- `data/chromadb/` — ChromaDB 向量数据
- `data/uploads/` — 上传文件

### 常用命令

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重新构建（代码变更后）
docker-compose up -d --build

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 进入容器
docker exec -it myrag-backend /bin/bash
```

---

## 配置说明

MyRAG 的配置采用 **三层加载** 机制（优先级从高到低）：

1. **环境变量** — 运行时注入
2. **`.env` 文件** — 项目根目录
3. **代码默认值** — `backend/app/config/settings.py`

完整的配置项列表请参见 [.env.example](.env.example) 文件，每个配置项都附带详细说明。

### 关键配置速查

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | **必需** DeepSeek API 密钥 | — |
| `APP_DEBUG` | 调试模式 | `true` |
| `DATABASE_URL` | 数据库连接串 | `sqlite+aiosqlite:///./data/myrag.db` |
| `JWT_SECRET_KEY` | JWT 签名密钥（生产必改） | `change-me-in-production` |
| `LLM_BACKEND` | LLM 后端类型 | `deepseek` |
| `EMBEDDING_BACKEND` | Embedding 后端 | `bge-small` |
| `VECTOR_STORE_BACKEND` | 向量数据库 | `chromadb` |

### 切换 LLM 后端示例

```bash
# 使用 OpenAI
LLM_BACKEND=openai
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini

# 使用本地 Ollama
LLM_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

---

## API 文档

启动后端后，Swagger 文档地址：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| GET | `/api/v1/users/me` | 获取当前用户 |
| GET | `/api/v1/datasets` | 数据集列表 |
| POST | `/api/v1/datasets` | 创建数据集 |
| GET | `/api/v1/datasets/{id}/documents` | 文档列表 |
| POST | `/api/v1/datasets/{id}/documents` | 上传文档 |
| GET | `/api/v1/conversations` | 对话列表 |
| POST | `/api/v1/conversations/{id}/messages` | 发送消息（SSE 流式） |
| GET | `/api/v1/admin/stats` | 系统统计（管理员） |

---

## 项目结构

```
myrag/
├── backend/                      # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py               # 应用入口 & 生命周期
│   │   ├── config/               # 配置管理（Settings 类、config.yaml）
│   │   ├── api/                   # API 路由（v1 版本、异常处理、依赖注入）
│   │   ├── models/               # SQLAlchemy ORM 模型
│   │   ├── schemas/              # Pydantic 请求/响应模型
│   │   ├── services/             # 业务逻辑层
│   │   │   ├── user_service.py
│   │   │   ├── dataset_service.py
│   │   │   ├── document_service.py
│   │   │   ├── conversation_service.py
│   │   │   └── admin_service.py
│   │   ├── rag/                  # RAG 引擎
│   │   │   ├── interfaces/       # 抽象接口定义
│   │   │   ├── parsers/          # 文档解析器
│   │   │   ├── splitters/        # 文本切片器
│   │   │   ├── embeddings/       # Embedding 实现
│   │   │   ├── vector_stores/    # 向量数据库实现
│   │   │   ├── llms/             # LLM 实现
│   │   │   ├── retrievers/       # 检索器
│   │   │   ├── pipeline.py       # 文档处理管道
│   │   │   └── engine.py         # RAG 编排引擎
│   │   ├── core/                 # 基础设施
│   │   │   ├── container.py      # DI 容器
│   │   │   ├── database.py       # 数据库会话
│   │   │   ├── security.py       # JWT 鉴权
│   │   │   ├── storage/          # 文件存储实现
│   │   │   └── task_queue/       # 任务队列实现
│   │   └── tasks/                # 异步任务定义
│   ├── tests/                    # 测试
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                     # React 前端
│   ├── src/
│   │   ├── api/                  # API 客户端层
│   │   ├── components/           # 公共组件
│   │   ├── pages/                # 页面组件
│   │   ├── store/                # Zustand 状态管理
│   │   ├── types/                # TypeScript 类型
│   │   └── utils/                # 工具函数
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.ts
├── docs/                         # 项目文档
├── docker-compose.yml            # Docker 编排
├── .env.example                  # 环境变量模板
└── README.md                     # 本文件
```

---

## 开发指南

### 代码规范

- **Python**: 遵循 PEP 8，使用类型注解
- **TypeScript**: 严格模式，使用类型定义文件
- **提交信息**: 遵循 Conventional Commits 规范

### 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试（如配置）
cd frontend
npm run test
```

---

## License

[MIT](LICENSE)
