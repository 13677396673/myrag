"""管理后台服务 — 系统统计、用户管理等管理员功能

AdminService 提供管理后台所需的业务逻辑：
- 系统统计信息（用户数、文档数、对话数、切片数、今日活跃用户）
- 分页用户列表（管理员查看所有用户）

依赖:
    - DatabaseManager（异步数据库会话）
"""

from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.database import DatabaseManager
from app.core.exceptions import RagError
from app.models.chunk import Chunk
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.user import User
from app.schemas.admin import SystemStatsResponse
from app.schemas.user import UserResponse


# ════════════════════════════════════════════════════════════
# 业务异常
# ════════════════════════════════════════════════════════════


class AdminServiceError(RagError):
    """管理后台服务相关错误的基类"""

    def __init__(
        self,
        code: str = "admin_service_error",
        message: str = "管理后台服务错误",
        detail: object = None,
    ) -> None:
        super().__init__(code=code, message=message, detail=detail)


# ════════════════════════════════════════════════════════════
# 管理后台服务
# ════════════════════════════════════════════════════════════


class AdminService:
    """管理后台服务

    提供系统统计信息查询和用户管理等功能，供管理后台使用。
    所有公开方法均为 async，需要外部注入 DatabaseManager。

    用法::

        service = AdminService(db_manager)
        stats = await service.get_stats()
        users, total = await service.list_users(page=1, page_size=20)
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ── 系统统计 ──────────────────────────────────────────────

    async def get_stats(self) -> SystemStatsResponse:
        """获取系统统计信息

        统计内容：
            - 用户总数
            - 文档总数
            - 对话总数
            - 切片总数
            - 今日活跃用户数（updated_at 为今天的用户数量）
        """
        async with self._db.get_session() as session:
            # 用户总数
            total_users: int = (
                await session.execute(select(func.count(User.id)))
            ).scalar() or 0

            # 文档总数
            total_documents: int = (
                await session.execute(select(func.count(Document.id)))
            ).scalar() or 0

            # 对话总数
            total_conversations: int = (
                await session.execute(select(func.count(Conversation.id)))
            ).scalar() or 0

            # 切片总数
            total_chunks: int = (
                await session.execute(select(func.count(Chunk.id)))
            ).scalar() or 0

            # 今日活跃用户数：updated_at >= 今天 00:00:00
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            active_users_today: int = (
                await session.execute(
                    select(func.count(User.id)).where(
                        User.updated_at >= today_start
                    )
                )
            ).scalar() or 0

            return SystemStatsResponse(
                total_users=total_users,
                total_documents=total_documents,
                total_conversations=total_conversations,
                total_chunks=total_chunks,
                active_users_today=active_users_today,
            )

    # ── 用户列表（分页） ──────────────────────────────────────

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取用户列表（分页），按创建时间倒序

        参数:
            page: 页码，从 1 开始
            page_size: 每页条数

        返回:
            {"users": [UserResponse, ...], "total": int}
        """
        async with self._db.get_session() as session:
            # 总数
            total: int = (
                await session.execute(select(func.count(User.id)))
            ).scalar() or 0

            # 分页查询
            offset = (page - 1) * page_size
            result = await session.execute(
                select(User)
                .order_by(User.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            users = result.scalars().all()

            return {
                "users": [self._to_user_response(u) for u in users],
                "total": total,
            }

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
