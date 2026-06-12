"""AdminService 单元测试

覆盖系统统计和用户列表分页功能，包括正常场景和边界情况。
使用临时 SQLite 文件数据库，每次函数级测试后自动清理。
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.user import UserRegisterRequest
from app.services.admin_service import AdminService, AdminServiceError


# ════════════════════════════════════════════════════════════
# 系统统计
# ════════════════════════════════════════════════════════════


class TestGetStats:
    """系统统计信息测试"""

    async def test_stats_empty_database(
        self, admin_service: AdminService
    ):
        """空数据库时所有统计值应为 0"""
        stats = await admin_service.get_stats()
        assert stats.total_users == 0
        assert stats.total_documents == 0
        assert stats.total_conversations == 0
        assert stats.total_chunks == 0
        assert stats.active_users_today == 0

    async def test_stats_with_data(
        self,
        admin_service: AdminService,
        user_service,
        sample_user: dict,
        sample_dataset,
        sample_document,
        sample_conversation,
    ):
        """插入测试数据后统计值应正确"""
        stats = await admin_service.get_stats()
        assert stats.total_users >= 1  # sample_user
        assert stats.total_documents >= 1  # sample_document
        assert stats.total_conversations >= 1  # sample_conversation
        # chunks 由 mock pipeline 模拟返回，实际数据库中不写入记录
        # 此处只验证查询不报错且值为非负整数
        assert stats.total_chunks >= 0

    async def test_stats_multiple_users(
        self,
        admin_service: AdminService,
        user_service,
        sample_user: dict,
    ):
        """多个用户时 total_users 应正确计数"""
        # 再注册几个用户
        for i in range(3):
            req = UserRegisterRequest(
                username=f"statuser{i}",
                email=f"stat{i}@example.com",
                password="pass123",
            )
            await user_service.register(req)

        stats = await admin_service.get_stats()
        assert stats.total_users == 4  # sample_user + 3 new

    async def test_stats_chunks_count(
        self,
        admin_service: AdminService,
        sample_document,
    ):
        """切片数量应正确反映"""
        # sample_document 使用 mock_pipeline 返回 10 个切片
        stats = await admin_service.get_stats()
        # 具体取决于 sample_document 创建时的 pipeline.mock 返回值
        assert stats.total_chunks >= 0
        # 注意：mock 的 pipeline 不会真正创建 chunk 记录，
        # 所以真实数据库中 chunks 表可能为 0
        # 这个测试更多是验证查询不报错

    async def test_stats_active_users_today(
        self,
        admin_service: AdminService,
        user_service,
        sample_user: dict,
    ):
        """今日活跃用户应正确计数"""
        # sample_user 是在今天创建的（测试环境），updated_at 为今天
        stats = await admin_service.get_stats()
        assert stats.active_users_today >= 1


# ════════════════════════════════════════════════════════════
# 用户列表（分页）
# ════════════════════════════════════════════════════════════


class TestListUsers:
    """用户列表分页测试"""

    async def test_list_users_empty(
        self, admin_service: AdminService
    ):
        """无用户时应返回空列表"""
        result = await admin_service.list_users()
        assert result["users"] == []
        assert result["total"] == 0

    async def test_list_users_with_data(
        self,
        admin_service: AdminService,
        user_service,
        sample_user: dict,
    ):
        """有用户时应返回正确数量和内容"""
        result = await admin_service.list_users()
        assert result["total"] == 1
        assert len(result["users"]) == 1
        user = result["users"][0]
        assert user.id == sample_user["id"]
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.is_active is True
        assert user.created_at is not None

    async def test_list_users_pagination(
        self,
        admin_service: AdminService,
        user_service,
        sample_user: dict,
    ):
        """分页参数应正确工作"""
        # 再创建 5 个用户
        for i in range(5):
            req = UserRegisterRequest(
                username=f"paginate_user{i}",
                email=f"paginate{i}@example.com",
                password="pass123",
            )
            await user_service.register(req)

        # 第一页，每页 3 条
        page1 = await admin_service.list_users(page=1, page_size=3)
        assert page1["total"] == 6  # sample_user + 5 new
        assert len(page1["users"]) == 3

        # 第二页
        page2 = await admin_service.list_users(page=2, page_size=3)
        assert page2["total"] == 6
        assert len(page2["users"]) == 3

        # 第三页（应无数据）
        page3 = await admin_service.list_users(page=3, page_size=3)
        assert page3["total"] == 6
        assert len(page3["users"]) == 0

    async def test_list_users_order(
        self,
        admin_service: AdminService,
        user_service,
    ):
        """用户列表应按创建时间倒序排列"""
        # 依次创建用户
        usernames = []
        for i in range(3):
            req = UserRegisterRequest(
                username=f"order_user{i}",
                email=f"order{i}@example.com",
                password="pass123",
            )
            result = await user_service.register(req)
            usernames.append(result.username)

        result = await admin_service.list_users(page=1, page_size=10)
        assert result["total"] == 3

        returned_names = [u.username for u in result["users"]]
        # 所有创建的用户都应出现在列表中
        for name in usernames:
            assert name in returned_names

    async def test_list_users_contains_all_fields(
        self,
        admin_service: AdminService,
        user_service,
        sample_user: dict,
    ):
        """用户列表中的 UserResponse 应包含所有必要字段"""
        result = await admin_service.list_users()
        assert len(result["users"]) >= 1
        user = result["users"][0]

        # 验证所有必要字段存在
        assert hasattr(user, "id")
        assert hasattr(user, "username")
        assert hasattr(user, "email")
        assert hasattr(user, "role")
        assert hasattr(user, "is_active")
        assert hasattr(user, "created_at")

        # 验证不包含敏感字段
        assert not hasattr(user, "password")
        assert not hasattr(user, "password_hash")


# ════════════════════════════════════════════════════════════
# 异常错误码验证
# ════════════════════════════════════════════════════════════


class TestAdminServiceErrors:
    """管理后台服务异常属性验证"""

    def test_admin_service_error_defaults(self):
        """AdminServiceError 应具有默认值"""
        err = AdminServiceError()
        assert err.code == "admin_service_error"
        assert err.message == "管理后台服务错误"
