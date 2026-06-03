# M17：用户服务模块 (services/user_service)

**阶段**: Phase 5 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M04 Database、M05 Security、M02 Models、M03 Schemas

**参考设计**: [详细设计文档 Module-17](../详细设计文档.md#module-17-用户服务模块-servicesuser_service)

---

## 任务清单

### 1. UserService

- [ ] 创建 `backend/app/services/__init__.py`
- [ ] 创建 `backend/app/services/user_service.py`
  - [ ] `UserService` 类
  - [ ] `__init__(db: DatabaseManager, security: SecurityManager)`
  - [ ] `async register(request: UserRegisterRequest) -> TokenResponse`
    - [ ] 检查用户名唯一（不唯一 → 抛 ValueError）
    - [ ] 检查邮箱唯一（不唯一 → 抛 ValueError）
    - [ ] 创建用户并返回 TokenResponse
  - [ ] `async login(request: UserLoginRequest) -> TokenResponse`
    - [ ] 支持用户名或邮箱登录
    - [ ] 密码验证失败 → 抛 ValueError（不透露是用户名错还是密码错）
    - [ ] 检查 is_active
  - [ ] `async get_user(user_id: str) -> UserResponse`
    - [ ] 用户不存在 → 抛 ValueError
  - [ ] `async update_user(user_id: str, email: str = None) -> UserResponse`
  - [ ] `async change_password(user_id: str, old_password: str, new_password: str)`
    - [ ] 原密码不正确 → 抛 ValueError
  - [ ] `_create_token_response(user: User) -> TokenResponse`（内部方法）
  - [ ] `_to_user_response(user: User) -> UserResponse`（内部方法）

### 2. 测试

- [ ] 创建 `backend/app/services/tests/__init__.py`
- [ ] 创建 `backend/app/services/tests/conftest.py`
  - [ ] Fixture：内存 SQLite 的 DatabaseManager
  - [ ] Fixture：测试用 SecurityManager（固定秘钥）
  - [ ] Fixture：UserService 实例
  - [ ] Fixture：测试前创建表，测试后清理
- [ ] 创建 `backend/app/services/tests/test_user_service.py`
  - [ ] 测试注册成功 → 返回 TokenResponse
  - [ ] 测试重复用户名 → ValueError
  - [ ] 测试重复邮箱 → ValueError
  - [ ] 测试登录成功 → TokenResponse
  - [ ] 测试登录密码错误 → ValueError（消息不区分用户名/密码错误）
  - [ ] 测试被禁用用户登录 → ValueError
  - [ ] 测试获取用户信息
  - [ ] 测试获取不存在的用户 → ValueError
  - [ ] 测试修改密码成功
  - [ ] 测试修改密码原密码错误 → ValueError

### 3. 验证

- [ ] 服务可独立测试（不依赖 API 层）
- [ ] 数据库操作使用 async session
- [ ] `pytest backend/app/services/tests/test_user_service.py` 全部通过

---

## 验收标准

- [ ] 注册/登录/修改密码功能完整
- [ ] 密码通过 SecurityManager 哈希（不自行调用 bcrypt）
- [ ] 错误消息不透露内部信息（不区分"用户名不存在"和"密码错误"）
- [ ] 用户数据通过 JWT 关联
