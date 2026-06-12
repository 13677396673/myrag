"""管理后台 API 路由测试

覆盖：
- GET /api/v1/admin/users — 用户列表（需 admin）
- GET /api/v1/admin/stats — 系统统计（需 admin）
"""

from httpx import AsyncClient


class TestAdminUsers:
    """管理后台用户列表测试"""

    async def test_list_users_success(
        self, admin_client: AsyncClient, admin_auth_header: dict
    ):
        """管理员获取用户列表应返回 200"""
        resp = await admin_client.get(
            "/api/v1/admin/users", headers=admin_auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["username"] == "testuser"

    async def test_list_users_pagination(
        self, admin_client: AsyncClient, admin_auth_header: dict
    ):
        """分页参数应正确工作"""
        resp = await admin_client.get(
            "/api/v1/admin/users?page=1&page_size=10",
            headers=admin_auth_header,
        )
        assert resp.status_code == 200

    async def test_list_users_requires_admin(
        self, client: AsyncClient, auth_header: dict
    ):
        """非管理员访问应返回 403"""
        resp = await client.get(
            "/api/v1/admin/users", headers=auth_header
        )
        assert resp.status_code == 403

    async def test_list_users_no_token(self, client: AsyncClient):
        """未登录访问应返回 401"""
        resp = await client.get("/api/v1/admin/users")
        assert resp.status_code == 401


class TestAdminStats:
    """管理后台统计测试"""

    async def test_stats_success(
        self, admin_client: AsyncClient, admin_auth_header: dict
    ):
        """管理员获取统计信息应返回 200"""
        resp = await admin_client.get(
            "/api/v1/admin/stats", headers=admin_auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        stats = data["data"]
        assert stats["total_users"] == 10
        assert stats["total_documents"] == 100
        assert stats["total_conversations"] == 50
        assert stats["total_chunks"] == 5000
        assert stats["active_users_today"] == 3

    async def test_stats_requires_admin(
        self, client: AsyncClient, auth_header: dict
    ):
        """非管理员访问应返回 403"""
        resp = await client.get(
            "/api/v1/admin/stats", headers=auth_header
        )
        assert resp.status_code == 403
