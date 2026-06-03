# M05：安全模块 (core/security)

**阶段**: Phase 1 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M01 Config

**参考设计**: [详细设计文档 Module-05](../详细设计文档.md#module-05-安全模块-coresecurity)

---

## 任务清单

### 1. SecurityManager 类

- [ ] 创建 `backend/app/core/security.py`
  - [ ] 定义 `SecurityManager` 类
  - [ ] `__init__(self, settings: Settings)`
  - [ ] `hash_password(password: str) -> str` — bcrypt 哈希
  - [ ] `verify_password(plain: str, hashed: str) -> bool`
  - [ ] `create_access_token(user_id: str, role: str) -> str` — JWT 创建
    - [ ] 含 sub、role、exp、iat 字段
  - [ ] `verify_token(token: str) -> Optional[dict]` — JWT 验证
    - [ ] 过期返回 None
    - [ ] 无效签名返回 None

### 2. 测试

- [ ] 创建 `backend/app/core/tests/test_security.py`
  - [ ] 测试密码哈希和验证的往返
    - [ ] 正确密码验证通过
    - [ ] 错误密码验证失败
  - [ ] 测试 JWT 创建和验证的往返
    - [ ] 正确的 payload 返回
  - [ ] 测试过期 Token 返回 None
  - [ ] 测试无效 Token 返回 None
  - [ ] 测试不同用户的 Token 返回不同 user_id
  - [ ] 测试 Token 包含 role 信息

### 3. 验证

- [ ] 使用 `Settings(JWT_SECRET_KEY="test-secret")` 测试
- [ ] 不依赖真实数据库
- [ ] `pytest backend/app/core/tests/test_security.py` 全部通过

---

## 验收标准

- [ ] 密码不存明文，使用 bcrypt 哈希
- [ ] JWT 含过期时间、用户 ID、角色
- [ ] 过期 Token 优雅降级（返回 None 而非抛异常）
- [ ] 测试覆盖正常和异常场景
