# M22：API 路由模块 (api/v1)

**阶段**: Phase 6 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M17-M21 Services、M23 Container

**参考设计**: [详细设计文档 Module-22](../详细设计文档.md#module-22-api-路由模块-apiv1)

---

## 任务清单

### 1. 依赖注入与鉴权中间件

- [x] 创建 `backend/app/api/__init__.py`
- [x] 创建 `backend/app/api/deps.py`
  - [x] `bearer_scheme = HTTPBearer()`
  - [x] `async get_current_user_id(credentials, container) -> str`
    - [x] 验证 JWT Token
    - [x] 无效/过期 → 401
  - [x] `async require_admin(user_id, container) -> str`
    - [x] 检查用户 role == "admin"
    - [x] 非管理员 → 403

### 2. 认证路由

- [x] 创建 `backend/app/api/v1/__init__.py`
- [x] 创建 `backend/app/api/v1/auth.py`
  - [x] `POST /auth/register` — 调用 user_service.register
  - [x] `POST /auth/login` — 调用 user_service.login
  - [x] `POST /auth/refresh` — 刷新 Token（预留）
  - [x] 统一错误处理（ValueError → 400）

### 3. 用户路由

- [x] 创建 `backend/app/api/v1/users.py`
  - [x] `GET /users/me` — 获取当前用户信息
  - [x] `PUT /users/me` — 更新个人信息
  - [x] `PUT /users/me/password` — 修改密码

### 4. 数据集路由

- [x] 创建 `backend/app/api/v1/datasets.py`
  - [x] `GET /datasets` — 列表
  - [x] `POST /datasets` — 创建
  - [x] `GET /datasets/{id}` — 详情
  - [x] `PUT /datasets/{id}` — 更新
  - [x] `DELETE /datasets/{id}` — 删除

### 5. 文档路由

- [x] 创建 `backend/app/api/v1/documents.py`
  - [x] `GET /datasets/{dataset_id}/documents` — 文档列表
  - [x] `POST /datasets/{dataset_id}/documents` — 上传文档（multipart）
  - [x] `GET /documents/{id}` — 文档详情
  - [x] `DELETE /documents/{id}` — 删除文档
  - [x] `GET /documents/{id}/chunks` — 切片列表
  - [x] `GET /documents/{id}/status` — 处理状态

### 6. 对话路由

- [x] 创建 `backend/app/api/v1/conversations.py`
  - [x] `GET /conversations` — 列表
  - [x] `POST /conversations` — 创建
  - [x] `GET /conversations/{id}` — 详情
  - [x] `DELETE /conversations/{id}` — 删除
  - [x] `GET /conversations/{id}/messages` — 消息列表
  - [x] `POST /conversations/{id}/messages` — 发送消息（SSE 流式响应）

### 7. 管理后台路由

- [x] 创建 `backend/app/api/v1/admin.py`
  - [x] `GET /admin/users` — 用户列表（需要 admin）
  - [x] `GET /admin/stats` — 系统统计（需要 admin）

### 8. 路由注册

- [x] 在 `api/v1/__init__.py` 中创建 `v1_router = APIRouter(prefix="/api/v1")`
- [x] 注册所有子路由
- [x] 创建 `backend/app/api/errors.py`
  - [x] 全局异常处理器：ValueError → 400、HTTPException → 对应状态码、通用异常 → 500

### 9. 测试

- [x] 创建 `backend/app/api/tests/__init__.py`
- [x] 创建 `backend/app/api/tests/conftest.py`
  - [x] Fixture：创建 TestClient
  - [x] Fixture：Mock Container 中所有 Service
- [x] 创建 `backend/app/api/tests/test_auth_api.py`
  - [x] 测试注册接口
  - [x] 测试登录接口
  - [x] 测试无 Token 访问受保护接口 → 401
- [x] 创建 `backend/app/api/tests/test_datasets_api.py`
  - [x] 测试数据集 CRUD 接口
  - [x] 测试鉴权
- [x] 创建 `backend/app/api/tests/test_documents_api.py`
  - [x] 测试文档上传接口
  - [x] 测试文件类型校验
- [x] 创建 `backend/app/api/tests/test_conversations_api.py`
  - [x] 测试对话 CRUD
  - [x] 测试 SSE 流式响应

### 10. 验证

- [x] 所有路由可访问
- [x] 鉴权中间件正常工作
- [x] SSE 流式返回 Content-Type: text/event-stream
- [x] `pytest backend/app/api/tests/` 全部通过

---

## 验收标准

- [x] 所有接口路径符合概要设计
- [x] 统一响应格式 `{code, data, message}`
- [x] JWT 鉴权保护所有非认证接口
- [x] ValueError → 400, HTTPException → 对应状态码, 其他 → 500
- [x] SSE 流式接口适用于对话消息
