# M22：API 路由模块 (api/v1)

**阶段**: Phase 6 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M17-M21 Services、M23 Container

**参考设计**: [详细设计文档 Module-22](../详细设计文档.md#module-22-api-路由模块-apiv1)

---

## 任务清单

### 1. 依赖注入与鉴权中间件

- [ ] 创建 `backend/app/api/__init__.py`
- [ ] 创建 `backend/app/api/deps.py`
  - [ ] `bearer_scheme = HTTPBearer()`
  - [ ] `async get_current_user_id(credentials, container) -> str`
    - [ ] 验证 JWT Token
    - [ ] 无效/过期 → 401
  - [ ] `async require_admin(user_id, container) -> str`
    - [ ] 检查用户 role == "admin"
    - [ ] 非管理员 → 403

### 2. 认证路由

- [ ] 创建 `backend/app/api/v1/__init__.py`
- [ ] 创建 `backend/app/api/v1/auth.py`
  - [ ] `POST /auth/register` — 调用 user_service.register
  - [ ] `POST /auth/login` — 调用 user_service.login
  - [ ] `POST /auth/refresh` — 刷新 Token（预留）
  - [ ] 统一错误处理（ValueError → 400）

### 3. 用户路由

- [ ] 创建 `backend/app/api/v1/users.py`
  - [ ] `GET /users/me` — 获取当前用户信息
  - [ ] `PUT /users/me` — 更新个人信息
  - [ ] `PUT /users/me/password` — 修改密码

### 4. 数据集路由

- [ ] 创建 `backend/app/api/v1/datasets.py`
  - [ ] `GET /datasets` — 列表
  - [ ] `POST /datasets` — 创建
  - [ ] `GET /datasets/{id}` — 详情
  - [ ] `PUT /datasets/{id}` — 更新
  - [ ] `DELETE /datasets/{id}` — 删除

### 5. 文档路由

- [ ] 创建 `backend/app/api/v1/documents.py`
  - [ ] `GET /datasets/{dataset_id}/documents` — 文档列表
  - [ ] `POST /datasets/{dataset_id}/documents` — 上传文档（multipart）
  - [ ] `GET /documents/{id}` — 文档详情
  - [ ] `DELETE /documents/{id}` — 删除文档
  - [ ] `GET /documents/{id}/chunks` — 切片列表
  - [ ] `GET /documents/{id}/status` — 处理状态

### 6. 对话路由

- [ ] 创建 `backend/app/api/v1/conversations.py`
  - [ ] `GET /conversations` — 列表
  - [ ] `POST /conversations` — 创建
  - [ ] `GET /conversations/{id}` — 详情
  - [ ] `DELETE /conversations/{id}` — 删除
  - [ ] `GET /conversations/{id}/messages` — 消息列表
  - [ ] `POST /conversations/{id}/messages` — 发送消息（SSE 流式响应）

### 7. 管理后台路由

- [ ] 创建 `backend/app/api/v1/admin.py`
  - [ ] `GET /admin/users` — 用户列表（需要 admin）
  - [ ] `GET /admin/stats` — 系统统计（需要 admin）

### 8. 路由注册

- [ ] 在 `api/v1/__init__.py` 中创建 `v1_router = APIRouter(prefix="/api/v1")`
- [ ] 注册所有子路由
- [ ] 创建 `backend/app/api/errors.py`
  - [ ] 全局异常处理器：ValueError → 400、HTTPException → 对应状态码、通用异常 → 500

### 9. 测试

- [ ] 创建 `backend/app/api/tests/__init__.py`
- [ ] 创建 `backend/app/api/tests/conftest.py`
  - [ ] Fixture：创建 TestClient
  - [ ] Fixture：Mock Container 中所有 Service
- [ ] 创建 `backend/app/api/tests/test_auth_api.py`
  - [ ] 测试注册接口
  - [ ] 测试登录接口
  - [ ] 测试无 Token 访问受保护接口 → 401
- [ ] 创建 `backend/app/api/tests/test_datasets_api.py`
  - [ ] 测试数据集 CRUD 接口
  - [ ] 测试鉴权
- [ ] 创建 `backend/app/api/tests/test_documents_api.py`
  - [ ] 测试文档上传接口
  - [ ] 测试文件类型校验
- [ ] 创建 `backend/app/api/tests/test_conversations_api.py`
  - [ ] 测试对话 CRUD
  - [ ] 测试 SSE 流式响应

### 10. 验证

- [ ] 所有路由可访问
- [ ] 鉴权中间件正常工作
- [ ] SSE 流式返回 Content-Type: text/event-stream
- [ ] `pytest backend/app/api/tests/` 全部通过

---

## 验收标准

- [ ] 所有接口路径符合概要设计
- [ ] 统一响应格式 `{code, data, message}`
- [ ] JWT 鉴权保护所有非认证接口
- [ ] ValueError → 400, HTTPException → 对应状态码, 其他 → 500
- [ ] SSE 流式接口适用于对话消息
