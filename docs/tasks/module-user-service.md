# M17：用户服务模块 (services/user_service)

**阶段**: Phase 5 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M01 Config, M02 Models (User), M04 Database, M05 Security, M03 Schemas (User)

**参考设计**: [详细设计文档 Module-17](../详细设计文档.md#module-17-用户服务模块-servicesuser_service)

---

## 任务清单

### 1. 服务异常定义

- [x] 在 `backend/app/services/user_service.py` 中定义业务异常类
  - [x] `UserServiceError` — 用户服务异常基类（继承 `RagError`）
  - [x] `UserAlreadyExists` — 用户名或邮箱已被注册（含冲突字段信息）
  - [x] `UserNotFound` — 用户不存在
  - [x] `InvalidCredentials` — 用户名或密码错误（不透露具体哪个错误）
  - [x] `PasswordNotMatch` — 原密码不匹配
  - [x] `UserInactive` — 账户已被禁用

### 2. UserService 类

- [x] 更新 `backend/app/services/__init__.py` — 导出 UserService 及异常类
- [x] 创建 `backend/app/services/user_service.py`
  - [x] 定义 `UserService` 类
  - [x] `__init__(self, db: DatabaseManager, security: SecurityManager)`
  - [x] `register(request: UserRegisterRequest) -> UserResponse`
    - [x] 检查用户名唯一性（不唯一 → UserAlreadyExists）
    - [x] 检查邮箱唯一性（不唯一 → UserAlreadyExists）
    - [x] 密码哈希存储（bcrypt）
    - [x] 默认角色 "user"，默认激活
    - [x] 返回不含密码的用户信息
  - [x] `login(request: UserLoginRequest) -> TokenResponse`
    - [x] 通过用户名查找用户
    - [x] 密码验证失败 → InvalidCredentials（不透露是用户名错还是密码错）
    - [x] 检查 is_active → UserInactive
    - [x] 签发 JWT（含 sub、role）
    - [x] 返回 `access_token` + 用户信息
  - [x] `get_user_by_id(user_id: str) -> UserResponse`
    - [x] 用户不存在 → UserNotFound
  - [x] `update_user(user_id: str, request: UserUpdateRequest) -> UserResponse`
    - [x] 检查新邮箱唯一性
  - [x] `change_password(user_id: str, request: PasswordChangeRequest) -> None`
    - [x] 原密码不正确 → PasswordNotMatch
  - [x] `list_users(page=1, page_size=20) -> Tuple[list[UserResponse], int]`
    - [x] 按创建时间倒序排列
    - [x] 支持分页
    - [x] 返回总记录数
  - [x] `_get_user_by_username(session, username)` — 内部辅助方法
  - [x] `_to_user_response(user) -> UserResponse` — 静态转换方法

### 3. 测试

- [x] 创建 `backend/app/services/tests/__init__.py`
- [x] 创建 `backend/app/services/tests/conftest.py`
  - [x] Fixture：临时 SQLite 文件的 DatabaseManager
  - [x] Fixture：测试用 SecurityManager（固定秘钥）
  - [x] Fixture：UserService 实例
  - [x] Fixture：预创建的测试用户（sample_user）
- [x] 创建 `backend/app/services/tests/test_user_service.py`（30 项测试）
  - [x] **注册测试（4 项）** — 成功、重复用户名、重复邮箱、密码哈希
  - [x] **登录测试（5 项）** — 成功、密码错误、不存在用户、禁用用户、JWT 内容
  - [x] **获取用户测试（3 项）** — 成功、不存在、无密码字段
  - [x] **更新用户测试（4 项）** — 成功、邮箱冲突、不存在、空更新
  - [x] **修改密码测试（4 项）** — 成功、原密码错误、不存在用户、旧密码失效
  - [x] **用户列表测试（4 项）** — 空列表、有数据、分页、顺序
  - [x] **异常错误码验证（6 项）** — 所有异常类的 code/message 正确

### 4. 验证

- [x] `from app.services import UserService` 无报错
- [x] `UserService` 构造函数接受 `DatabaseManager` + `SecurityManager`
- [x] 所有公开方法正确使用 async session
- [x] 密码不存明文（bcrypt 哈希）
- [x] 过期/无效凭据不透露具体哪个字段错误
- [x] JWT 包含 sub (user_id) 和 role
- [x] `pytest backend/app/services/tests/` 全部通过（30 passed）

---

## 验收标准

- [x] 注册/登录/修改密码功能完整
- [x] 密码通过 SecurityManager 哈希（不自行调用 bcrypt）
- [x] 错误消息不透露安全敏感细节（不区分"用户名不存在"和"密码错误"）
- [x] 用户数据通过 JWT 关联
- [x] 测试覆盖正常流程和所有异常分支（30 项测试）
