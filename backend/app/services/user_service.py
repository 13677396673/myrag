"""用户服务 — 注册、登录、信息管理

UserService 封装了所有与用户相关的业务逻辑：
- 注册时检查用户名和邮箱唯一性
- 登录时验证密码并签发 JWT
- 支持用户信息查询与修改、密码修改
- 提供管理员用户列表分页查询

依赖:
    - DatabaseManager（异步数据库会话）
    - SecurityManager（密码哈希 + JWT）
"""

from typing import Optional, Tuple

from sqlalchemy import func, select

from app.core.database import DatabaseManager
from app.core.exceptions import RagError
from app.core.security import SecurityManager
from app.models.user import User
from app.schemas.user import (
    PasswordChangeRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)


# ════════════════════════════════════════════════════════════
# 业务异常
# ════════════════════════════════════════════════════════════


class UserServiceError(RagError):
    """用户服务相关错误的基类"""

    def __init__(
        self,
        code: str = "user_service_error",
        message: str = "用户服务错误",
        detail: object = None,
    ) -> None:
        super().__init__(code=code, message=message, detail=detail)


class UserAlreadyExists(UserServiceError):
    """用户名或邮箱已被注册"""

    def __init__(self, field: str, value: str) -> None:
        super().__init__(
            code="user_already_exists",
            message=f"该{field}已被注册",
            detail={field: value},
        )


class UserNotFound(UserServiceError):
    """用户不存在"""

    def __init__(self, user_id: str) -> None:
        super().__init__(
            code="user_not_found",
            message="用户不存在",
            detail={"user_id": user_id},
        )


class InvalidCredentials(UserServiceError):
    """用户名或密码错误"""

    def __init__(self) -> None:
        super().__init__(
            code="invalid_credentials",
            message="用户名或密码错误",
        )


class PasswordNotMatch(UserServiceError):
    """原密码不匹配"""

    def __init__(self) -> None:
        super().__init__(
            code="password_not_match",
            message="原密码错误",
        )


class UserInactive(UserServiceError):
    """用户已被禁用"""

    def __init__(self) -> None:
        super().__init__(
            code="user_inactive",
            message="该账户已被禁用，请联系管理员",
        )


# ════════════════════════════════════════════════════════════
# 用户服务
# ════════════════════════════════════════════════════════════


class UserService:
    """用户服务

    提供用户注册、登录、信息查询与修改、密码修改等功能。
    所有公开方法均为 async，需要外部注入 DatabaseManager 和 SecurityManager。

    用法::

        service = UserService(db_manager, security_manager)
        result = await service.register(request)
        token = await service.login(request)
    """

    def __init__(self, db: DatabaseManager, security: SecurityManager) -> None:
        self._db = db
        self._security = security

    # ── 注册 ──────────────────────────────────────────────────

    async def register(self, request: UserRegisterRequest) -> UserResponse:
        """用户注册

        流程:
            1. 检查用户名唯一性
            2. 检查邮箱唯一性
            3. 密码哈希
            4. 创建用户记录
            5. 返回用户公开信息

        异常:
            UserAlreadyExists — 用户名或邮箱已被占用
        """
        async with self._db.get_session() as session:
            # 检查用户名
            existing = await session.execute(
                select(User).where(User.username == request.username)
            )
            if existing.scalar_one_or_none():
                raise UserAlreadyExists("用户名", request.username)

            # 检查邮箱
            existing = await session.execute(
                select(User).where(User.email == request.email)
            )
            if existing.scalar_one_or_none():
                raise UserAlreadyExists("邮箱", request.email)

            # 创建用户
            hashed = self._security.hash_password(request.password)
            user = User(
                username=request.username,
                email=request.email,
                password_hash=hashed,
                role="user",
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            return self._to_user_response(user)

    # ── 登录 ──────────────────────────────────────────────────

    async def login(self, request: UserLoginRequest) -> TokenResponse:
        """用户登录

        流程:
            1. 根据用户名查找用户
            2. 验证密码
            3. 检查账户是否激活
            4. 签发 JWT
            5. 返回令牌 + 用户信息

        异常:
            InvalidCredentials — 用户名或密码错误
            UserInactive — 账户已被禁用
        """
        async with self._db.get_session() as session:
            user = await self._get_user_by_username(session, request.username)
            if user is None:
                raise InvalidCredentials()

            # 验证密码
            if not self._security.verify_password(request.password, user.password_hash):
                raise InvalidCredentials()

            # 检查账户状态
            if not user.is_active:
                raise UserInactive()

            # 签发 JWT
            token = self._security.create_access_token(
                user_id=user.id,
                role=user.role,
            )

            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user=self._to_user_response(user),
            )

    # ── 获取用户 ──────────────────────────────────────────────

    async def get_user_by_id(self, user_id: str) -> UserResponse:
        """根据用户 ID 获取用户公开信息

        异常:
            UserNotFound — 用户不存在
        """
        async with self._db.get_session() as session:
            user = await session.get(User, user_id)
            if user is None:
                raise UserNotFound(user_id)

            return self._to_user_response(user)

    # ── 更新用户 ──────────────────────────────────────────────

    async def update_user(
        self, user_id: str, request: UserUpdateRequest
    ) -> UserResponse:
        """更新用户信息（目前仅支持修改邮箱）

        异常:
            UserNotFound — 用户不存在
            UserAlreadyExists — 新邮箱已被其他用户使用
        """
        async with self._db.get_session() as session:
            user = await session.get(User, user_id)
            if user is None:
                raise UserNotFound(user_id)

            if request.email is not None:
                # 检查新邮箱是否被其他用户占用
                existing = await session.execute(
                    select(User).where(
                        User.email == request.email,
                        User.id != user_id,
                    )
                )
                if existing.scalar_one_or_none():
                    raise UserAlreadyExists("邮箱", request.email)
                user.email = request.email

            await session.commit()
            await session.refresh(user)

            return self._to_user_response(user)

    # ── 修改密码 ──────────────────────────────────────────────

    async def change_password(
        self, user_id: str, request: PasswordChangeRequest
    ) -> None:
        """修改用户密码

        需要验证原密码正确性，验证通过后更新为新密码。

        异常:
            UserNotFound — 用户不存在
            PasswordNotMatch — 原密码错误
        """
        async with self._db.get_session() as session:
            user = await session.get(User, user_id)
            if user is None:
                raise UserNotFound(user_id)

            # 验证原密码
            if not self._security.verify_password(
                request.old_password, user.password_hash
            ):
                raise PasswordNotMatch()

            # 更新密码
            user.password_hash = self._security.hash_password(request.new_password)
            await session.commit()

    # ── 管理员：用户列表 ──────────────────────────────────────

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[list[UserResponse], int]:
        """获取用户列表（分页），按创建时间倒序

        返回:
            (用户列表, 总记录数)
        """
        async with self._db.get_session() as session:
            # 总数
            count_result = await session.execute(select(func.count(User.id)))
            total: int = count_result.scalar() or 0

            # 分页查询
            offset = (page - 1) * page_size
            result = await session.execute(
                select(User)
                .order_by(User.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            users = result.scalars().all()

            return [self._to_user_response(u) for u in users], total

    # ── 内部辅助 ──────────────────────────────────────────────

    @staticmethod
    def _to_user_response(user: User) -> UserResponse:
        """将 User ORM 对象转换为 UserResponse Pydantic 模式"""
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    @staticmethod
    async def _get_user_by_username(session, username: str) -> Optional[User]:
        """通过用户名查询用户（内部方法，需在会话内调用）"""
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
