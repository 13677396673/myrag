"""主入口模块 (main.py) 测试

覆盖：
- 应用配置（title, version, docs_url）
- 健康检查端点 ``GET /health``
- CORS 中间件
- 全局异常处理器
- 生命周期事件（startup / shutdown）
"""

import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import ASGITransport, AsyncClient

from app.config.settings import Settings
from app.core.container import Container
from app.main import create_app


# ════════════════════════════════════════════════════════════
# 夹具
# ════════════════════════════════════════════════════════════


@pytest.fixture(scope="function")
def sqlite_db_path() -> str:
    """创建临时 SQLite 数据库文件路径，测试结束后清理"""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="rag_test_main_")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def test_settings(sqlite_db_path: str) -> Settings:
    """返回指向临时 SQLite 文件的测试配置"""
    return Settings(
        DATABASE_URL=f"sqlite+aiosqlite:///{sqlite_db_path}",
        DATABASE_ECHO=False,
        JWT_SECRET_KEY="test-secret",
        JWT_ALGORITHM="HS256",
        SERVER_CORS_ORIGINS=["http://localhost:3000", "https://example.com"],
    )


@pytest.fixture(scope="function")
def app(test_settings: Settings) -> FastAPI:
    """创建使用测试配置的 FastAPI 应用实例"""
    return create_app(settings=test_settings)


@pytest.fixture(scope="function")
async def client(app: FastAPI) -> AsyncClient:
    """返回 HTTP 测试客户端（自动触发 lifespan 事件）"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ════════════════════════════════════════════════════════════
# 应用配置
# ════════════════════════════════════════════════════════════


class TestAppConfiguration:
    """应用基本配置验证"""

    def test_app_title(self, app: FastAPI):
        """应用标题应为 MyRAG API"""
        assert app.title == "MyRAG API"

    def test_app_version(self, app: FastAPI):
        """应用版本应与 settings 一致"""
        assert app.version == "0.1.0"

    def test_docs_url(self, app: FastAPI):
        """Swagger 文档路径应为 /docs"""
        assert app.docs_url == "/docs"

    def test_openapi_available(self, app: FastAPI):
        """OpenAPI schema 应可生成"""
        assert app.openapi() is not None
        assert app.openapi()["info"]["title"] == "MyRAG API"

    def test_cors_middleware_registered(self, app: FastAPI):
        """CORS 中间件应已注册"""
        middleware_types = [m.cls for m in app.user_middleware]
        assert CORSMiddleware in middleware_types

    def test_v1_router_included(self, app: FastAPI):
        """v1 路由应已挂载"""
        routes = [r.path for r in app.routes]
        assert "/api/v1/auth/register" in routes
        assert "/api/v1/users/me" in routes
        assert "/api/v1/datasets" in routes
        assert "/api/v1/admin/stats" in routes

    def test_health_route_included(self, app: FastAPI):
        """健康检查路由应已注册"""
        routes = [r.path for r in app.routes]
        assert "/health" in routes


# ════════════════════════════════════════════════════════════
# 健康检查
# ════════════════════════════════════════════════════════════


class TestHealthCheck:
    """健康检查端点测试"""

    async def test_health_returns_200(self, client: AsyncClient):
        """健康检查应返回 200"""
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_health_returns_ok_status(self, client: AsyncClient):
        """健康检查应返回 status=ok"""
        resp = await client.get("/health")
        data = resp.json()
        assert data["status"] == "ok"

    async def test_health_returns_version(self, client: AsyncClient):
        """健康检查应返回版本号"""
        resp = await client.get("/health")
        data = resp.json()
        assert data["version"] == "0.1.0"

    async def test_health_no_auth_required(self, client: AsyncClient):
        """健康检查不需要认证"""
        resp = await client.get("/health")
        assert resp.status_code == 200


# ════════════════════════════════════════════════════════════
# CORS
# ════════════════════════════════════════════════════════════


class TestCORS:
    """CORS 中间件测试"""

    async def test_cors_allowed_origin(self, client: AsyncClient):
        """允许的来源应返回正确的 CORS 头"""
        resp = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

    async def test_cors_another_allowed_origin(self, client: AsyncClient):
        """另一个允许的来源也应有正确的 CORS 头"""
        resp = await client.options(
            "/health",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "https://example.com"

    async def test_cors_disallowed_origin_returns_none(self, app: FastAPI, test_settings: Settings):
        """未配置的来源不应返回 access-control-allow-origin"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.options(
                "/health",
                headers={
                    "Origin": "https://evil.com",
                    "Access-Control-Request-Method": "GET",
                },
            )
            # CORSMiddleware 在未配置的来源上返回 None（不暴露 origin）
            cors_header = resp.headers.get("access-control-allow-origin")
            assert cors_header is None or cors_header not in test_settings.SERVER_CORS_ORIGINS

    async def test_cors_headers_on_get(self, client: AsyncClient):
        """GET 请求也应返回 CORS 头"""
        resp = await client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


# ════════════════════════════════════════════════════════════
# 异常处理器
# ════════════════════════════════════════════════════════════


class TestExceptionHandlers:
    """全局异常处理器测试"""

    async def test_404_returns_json(self, client: AsyncClient):
        """不存在的路由应返回 JSON（FastAPI 默认格式）"""
        resp = await client.get("/nonexistent-route")
        assert resp.status_code == 404
        data = resp.json()
        # FastAPI 默认 404 返回 {"detail": "Not Found"}
        assert "detail" in data

    async def test_422_returns_json(self, client: AsyncClient):
        """参数校验错误应返回 422 JSON"""
        resp = await client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 422
        data = resp.json()
        assert isinstance(data, dict)
        assert "detail" in data

    async def test_value_error_returns_400(self, app: FastAPI, test_settings: Settings):
        """ValueError 应被转为 400 JSON"""
        # 临时注册一个会抛出 ValueError 的路由
        @app.get("/test-value-error")
        async def trigger_value_error():
            raise ValueError("测试参数错误")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/test-value-error")
            assert resp.status_code == 400
            data = resp.json()
            assert data["message"] == "测试参数错误"
            assert data["code"] == 400

    def test_exception_handler_registered(self, app: FastAPI):
        """异常处理器应已注册"""
        from fastapi import HTTPException

        handler_excs = list(app.exception_handlers.keys())
        assert ValueError in handler_excs
        assert HTTPException in handler_excs
        assert Exception in handler_excs


# ════════════════════════════════════════════════════════════
# 生命周期
# ════════════════════════════════════════════════════════════


class TestLifecycle:
    """生命周期事件测试"""

    async def _trigger_startup(self, app: FastAPI) -> None:
        """触发应用的所有 startup 事件"""
        for handler in app.router.on_startup:
            await handler()

    async def _trigger_shutdown(self, app: FastAPI) -> None:
        """触发应用的所有 shutdown 事件"""
        for handler in app.router.on_shutdown:
            await handler()

    async def test_startup_initializes_container(self, test_settings: Settings):
        """Startup 事件应初始化全局 Container"""
        # 确保无残留全局容器
        Container.clear_container()
        assert not hasattr(Container, "_global_container") or Container._global_container is None  # noqa: E501

        app = create_app(settings=test_settings)

        # 直接触发 startup 事件
        # (ASGITransport 在 httpx 0.28 中不自动处理 lifespan)
        await self._trigger_startup(app)

        # 验证容器已初始化
        assert hasattr(Container, "_global_container")
        assert Container._global_container is not None

        # 健康检查可用
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/health")
            assert resp.status_code == 200

        # 触发 shutdown
        await self._trigger_shutdown(app)

        # 容器应被清理
        assert not hasattr(Container, "_global_container") or Container._global_container is None  # noqa: E501

    async def test_double_lifecycle(self, test_settings: Settings):
        """多次启动/关闭不应出错"""
        Container.clear_container()

        app1 = create_app(settings=test_settings)
        await self._trigger_startup(app1)

        transport1 = ASGITransport(app=app1)
        async with AsyncClient(transport=transport1, base_url="http://test") as ac1:
            resp = await ac1.get("/health")
            assert resp.status_code == 200

        await self._trigger_shutdown(app1)
        Container.clear_container()

        app2 = create_app(settings=test_settings)
        await self._trigger_startup(app2)

        transport2 = ASGITransport(app=app2)
        async with AsyncClient(transport=transport2, base_url="http://test") as ac2:
            resp = await ac2.get("/health")
            assert resp.status_code == 200

        await self._trigger_shutdown(app2)
        Container.clear_container()
