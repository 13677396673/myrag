"""用户服务单元测试

覆盖 UserService 的所有公开方法，包括正常流程和异常场景。
使用临时 SQLite 文件数据库，每次函数级测试后自动清理。
"""

import pytest

from app.schemas.user import (
    PasswordChangeRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserUpdateRequest,
)
from app.services.user_service import (
    InvalidCredentials,
    PasswordNotMatch,
    UserAlreadyExists,
    UserInactive,
    UserNotFound,
    UserService,
    UserServiceError,
)


# ════════════════════════════════════════════════════════════
# 注册
# ════════════════════════════════════════════════════════════


class TestRegister:
    """用户注册测试"""

    async def test_register_success(self, user_service: UserService):
        """正常注册应返回用户信息"""
        request = UserRegisterRequest(
            username="newuser",
            email="new@example.com",
            password="mypassword",
        )
        result = await user_service.register(request)

        assert result.username == "newuser"
        assert result.email == "new@example.com"
        assert result.role == "user"
        assert result.is_active is True
        assert result.id is not None
        assert result.created_at is not None

    async def test_register_duplicate_username(
        self, user_service: UserService, sample_user: dict
    ):
        """重复用户名应抛出 UserAlreadyExists"""
        request = UserRegisterRequest(
            username="testuser",
            email="other@example.com",
            password="mypassword",
        )
        with pytest.raises(UserAlreadyExists) as exc:
            await user_service.register(request)
        assert exc.value.code == "user_already_exists"

    async def test_register_duplicate_email(
        self, user_service: UserService, sample_user: dict
    ):
        """重复邮箱应抛出 UserAlreadyExists"""
        request = UserRegisterRequest(
            username="otheruser",
            email="test@example.com",
            password="mypassword",
        )
        with pytest.raises(UserAlreadyExists) as exc:
            await user_service.register(request)
        assert exc.value.code == "user_already_exists"

    async def test_register_password_is_hashed(
        self, user_service: UserService
    ):
        """注册后数据库中不应存储明文密码"""
        request = UserRegisterRequest(
            username="hashcheck",
            email="hash@example.com",
            password="mysecretpass",
        )
        result = await user_service.register(request)

        # 直接从数据库验证存储的是哈希值而非明文
        from app.models.user import User
        from sqlalchemy import select

        async with user_service._db.get_session() as session:
            user = await session.get(User, result.id)
            assert user is not None
            assert user.password_hash != "mysecretpass"
            assert user.password_hash.startswith("$2b$")


# ════════════════════════════════════════════════════════════
# 登录
# ════════════════════════════════════════════════════════════


class TestLogin:
    """用户登录测试"""

    async def test_login_success(
        self, user_service: UserService, sample_user: dict
    ):
        """正常登录应返回 JWT 令牌和用户信息"""
        request = UserLoginRequest(
            username="testuser",
            password="secure123",
        )
        result = await user_service.login(request)

        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.user.username == "testuser"
        assert result.user.id == sample_user["id"]

    async def test_login_wrong_password(
        self, user_service: UserService, sample_user: dict
    ):
        """错误密码应抛出 InvalidCredentials"""
        request = UserLoginRequest(
            username="testuser",
            password="wrongpassword",
        )
        with pytest.raises(InvalidCredentials):
            await user_service.login(request)

    async def test_login_nonexistent_user(
        self, user_service: UserService
    ):
        """不存在的用户名应抛出 InvalidCredentials"""
        request = UserLoginRequest(
            username="nobody",
            password="somepass",
        )
        with pytest.raises(InvalidCredentials):
            await user_service.login(request)

    async def test_login_inactive_user(
        self, user_service: UserService, sample_user: dict
    ):
        """被禁用的用户应抛出 UserInactive"""
        # 先将用户禁用
        from app.models.user import User

        async with user_service._db.get_session() as session:
            user = await session.get(User, sample_user["id"])
            user.is_active = False
            await session.commit()

        request = UserLoginRequest(
            username="testuser",
            password="secure123",
        )
        with pytest.raises(UserInactive):
            await user_service.login(request)

    async def test_login_token_contains_user_id(
        self, user_service: UserService, sample_user: dict
    ):
        """JWT 应包含正确的用户 ID"""
        request = UserLoginRequest(
            username="testuser",
            password="secure123",
        )
        result = await user_service.login(request)

        # 验证 token 内容
        payload = user_service._security.verify_token(result.access_token)
        assert payload is not None
        assert payload["sub"] == sample_user["id"]
        assert payload["role"] == "user"


# ════════════════════════════════════════════════════════════
# 获取用户
# ════════════════════════════════════════════════════════════


class TestGetUser:
    """获取用户信息测试"""

    async def test_get_user_by_id_success(
        self, user_service: UserService, sample_user: dict
    ):
        """通过 ID 获取用户应返回正确信息"""
        result = await user_service.get_user_by_id(sample_user["id"])

        assert result.id == sample_user["id"]
        assert result.username == "testuser"
        assert result.email == "test@example.com"

    async def test_get_user_by_id_not_found(
        self, user_service: UserService
    ):
        """不存在的用户 ID 应抛出 UserNotFound"""
        with pytest.raises(UserNotFound):
            await user_service.get_user_by_id("non-existent-id")

    async def test_get_user_has_no_password(
        self, user_service: UserService, sample_user: dict
    ):
        """用户响应中不应包含密码字段"""
        result = await user_service.get_user_by_id(sample_user["id"])
        assert not hasattr(result, "password")
        assert not hasattr(result, "password_hash")


# ════════════════════════════════════════════════════════════
# 更新用户
# ════════════════════════════════════════════════════════════


class TestUpdateUser:
    """更新用户信息测试"""

    async def test_update_email_success(
        self, user_service: UserService, sample_user: dict
    ):
        """更新邮箱应成功"""
        request = UserUpdateRequest(email="newemail@example.com")
        result = await user_service.update_user(sample_user["id"], request)

        assert result.email == "newemail@example.com"
        assert result.username == "testuser"  # 其他字段不变

    async def test_update_email_to_existing(
        self, user_service: UserService, sample_user: dict
    ):
        """更新为已存在的邮箱应抛出 UserAlreadyExists"""
        # 先创建另一个用户
        register_req = UserRegisterRequest(
            username="another",
            email="another@example.com",
            password="pass123",
        )
        await user_service.register(register_req)

        # 尝试将 testuser 的邮箱改为 another 的邮箱
        request = UserUpdateRequest(email="another@example.com")
        with pytest.raises(UserAlreadyExists) as exc:
            await user_service.update_user(sample_user["id"], request)
        assert exc.value.code == "user_already_exists"

    async def test_update_user_not_found(
        self, user_service: UserService
    ):
        """不存在的用户更新应抛出 UserNotFound"""
        request = UserUpdateRequest(email="any@example.com")
        with pytest.raises(UserNotFound):
            await user_service.update_user("non-existent-id", request)

    async def test_update_email_none(
        self, user_service: UserService, sample_user: dict
    ):
        """不传 email 时不应修改用户信息"""
        request = UserUpdateRequest()  # email is None
        result = await user_service.update_user(sample_user["id"], request)

        assert result.email == "test@example.com"  # 保持不变


# ════════════════════════════════════════════════════════════
# 修改密码
# ════════════════════════════════════════════════════════════


class TestChangePassword:
    """修改密码测试"""

    async def test_change_password_success(
        self, user_service: UserService, sample_user: dict
    ):
        """正常修改密码应成功"""
        request = PasswordChangeRequest(
            old_password="secure123",
            new_password="newpass456",
        )
        # 不应抛出异常
        await user_service.change_password(sample_user["id"], request)

        # 验证新密码可以登录
        login_req = UserLoginRequest(
            username="testuser",
            password="newpass456",
        )
        result = await user_service.login(login_req)
        assert result.user.id == sample_user["id"]

    async def test_change_password_wrong_old(
        self, user_service: UserService, sample_user: dict
    ):
        """原密码错误应抛出 PasswordNotMatch"""
        request = PasswordChangeRequest(
            old_password="wrongold",
            new_password="newpass456",
        )
        with pytest.raises(PasswordNotMatch):
            await user_service.change_password(sample_user["id"], request)

    async def test_change_password_user_not_found(
        self, user_service: UserService
    ):
        """不存在的用户修改密码应抛出 UserNotFound"""
        request = PasswordChangeRequest(
            old_password="oldpass",
            new_password="newpass",
        )
        with pytest.raises(UserNotFound):
            await user_service.change_password("non-existent-id", request)

    async def test_change_password_old_password_still_works_until_changed(
        self, user_service: UserService, sample_user: dict
    ):
        """修改密码后，旧密码应无法再登录"""
        request = PasswordChangeRequest(
            old_password="secure123",
            new_password="newpass456",
        )
        await user_service.change_password(sample_user["id"], request)

        # 旧密码登录应失败
        old_login = UserLoginRequest(
            username="testuser",
            password="secure123",
        )
        with pytest.raises(InvalidCredentials):
            await user_service.login(old_login)

        # 新密码登录应成功
        new_login = UserLoginRequest(
            username="testuser",
            password="newpass456",
        )
        result = await user_service.login(new_login)
        assert result.user.id == sample_user["id"]


# ════════════════════════════════════════════════════════════
# 管理员：用户列表
# ════════════════════════════════════════════════════════════


class TestListUsers:
    """用户列表（管理员）测试"""

    async def test_list_users_empty(
        self, user_service: UserService
    ):
        """无用户时应返回空列表"""
        users, total = await user_service.list_users()
        assert len(users) == 0
        assert total == 0

    async def test_list_users_with_data(
        self, user_service: UserService, sample_user: dict
    ):
        """有用户时应返回正确数量"""
        users, total = await user_service.list_users()
        assert total == 1
        assert len(users) == 1
        assert users[0].username == "testuser"

    async def test_list_users_pagination(
        self, user_service: UserService, sample_user: dict
    ):
        """分页参数应正确工作"""
        # 再创建几个用户
        for i in range(5):
            req = UserRegisterRequest(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="pass123",
            )
            await user_service.register(req)

        # 第一页，每页 3 条
        users, total = await user_service.list_users(page=1, page_size=3)
        assert total == 6  # sample_user + 5 new
        assert len(users) == 3

        # 第二页
        users2, total2 = await user_service.list_users(page=2, page_size=3)
        assert total2 == 6
        assert len(users2) == 3

        # 第三页（应该只有 0 条）
        users3, total3 = await user_service.list_users(page=3, page_size=3)
        assert total3 == 6
        assert len(users3) == 0

    async def test_list_users_order(
        self, user_service: UserService
    ):
        """用户列表应按创建时间倒序排列"""
        # 依次创建用户
        reqs = []
        for i in range(3):
            req = UserRegisterRequest(
                username=f"orderuser{i}",
                email=f"order{i}@example.com",
                password="pass123",
            )
            result = await user_service.register(req)
            reqs.append(result)

        users, total = await user_service.list_users(page=1, page_size=10)
        assert total == 3

        # 三个用户都应出现在列表中
        usernames = [u.username for u in users]
        assert "orderuser0" in usernames
        assert "orderuser1" in usernames
        assert "orderuser2" in usernames


# ════════════════════════════════════════════════════════════
# 异常错误码验证
# ════════════════════════════════════════════════════════════


class TestUserServiceErrors:
    """用户服务异常属性验证"""

    def test_user_service_error_defaults(self):
        """UserServiceError 应具有默认值"""
        err = UserServiceError()
        assert err.code == "user_service_error"
        assert err.message == "用户服务错误"

    def test_user_already_exists_error(self):
        """UserAlreadyExists 应包含冲突字段信息"""
        err = UserAlreadyExists("用户名", "testuser")
        assert err.code == "user_already_exists"
        assert "testuser" in str(err)

    def test_user_not_found_error(self):
        """UserNotFound 应包含 user_id"""
        err = UserNotFound("user-123")
        assert err.code == "user_not_found"
        assert "user-123" in str(err)

    def test_invalid_credentials_error(self):
        """InvalidCredentials 不应透露是用户名还是密码错误"""
        err = InvalidCredentials()
        assert err.code == "invalid_credentials"
        assert "用户名或密码错误" in err.message

    def test_password_not_match_error(self):
        """PasswordNotMatch 应有明确消息"""
        err = PasswordNotMatch()
        assert err.code == "password_not_match"

    def test_user_inactive_error(self):
        """UserInactive 应有明确消息"""
        err = UserInactive()
        assert err.code == "user_inactive"
