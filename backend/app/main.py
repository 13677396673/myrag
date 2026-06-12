"""FastAPI 应用主入口

创建 FastAPI 应用实例，配置 CORS、异常处理器、路由和生命周期事件。
应用通过 ``Container`` 管理所有依赖组件的初始化和释放。

启动方式::

    uvicorn app.main:app --reload

或通过 ``run.py``::

    python run.py
"""

import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.v1 import v1_router
from app.config.settings import Settings
from app.core.container import Container

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# 应用工厂
# ════════════════════════════════════════════════════════════


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """创建并配置 FastAPI 应用实例

    参数:
        settings: 应用配置。若为 ``None``（默认），从环境变量 / ``.env`` 自动加载。

    返回:
        配置完整的 FastAPI 实例
    """
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title="MyRAG API",
        version=settings.APP_VERSION,
        docs_url="/docs",
    )

    # ── CORS 中间件 ────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.SERVER_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── 异常处理器 ─────────────────────────────────────────
    register_exception_handlers(app)

    # ── 路由 ───────────────────────────────────────────────
    app.include_router(v1_router)

    # ── 健康检查 ───────────────────────────────────────────
    @app.get("/health", tags=["系统"])
    async def health_check():
        """服务健康检查

        返回服务状态和版本号，不依赖数据库或外部服务，
        可用于负载均衡器的健康探测。
        """
        return {"status": "ok", "version": settings.APP_VERSION}

    # ── 生命周期事件 ───────────────────────────────────────

    @app.on_event("startup")
    async def startup():
        """应用启动时初始化 DI 容器

        1. 创建 ``Container(settings)``
        2. 初始化数据库引擎并建表
        3. 设为全局单例，供 ``Depends(get_container)`` 使用
        """
        container = Container(settings)
        await container.initialize()
        Container.set_container(container)
        logger.info(
            "应用启动完成 | 数据库已初始化 | version=%s", settings.APP_VERSION
        )

    @app.on_event("shutdown")
    async def shutdown():
        """应用关闭时释放 DI 容器资源

        关闭数据库连接池，清除全局容器引用。
        """
        try:
            if hasattr(Container, "_global_container") and Container._global_container is not None:  # type: ignore[has-type]  # noqa: E501
                await Container._global_container.close()
                Container.clear_container()
                logger.info("应用已关闭 | 数据库连接已释放")
        except AttributeError:
            pass

    return app


# 模块级应用实例，供 uvicorn 直接导入使用
app = create_app()
