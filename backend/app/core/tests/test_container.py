"""Container 单元测试

覆盖：
- Container 创建与生命周期管理（initialize / close）
- 懒加载验证（属性访问前不初始化其他组件）
- 核心基础设施组件访问（security, storage, task_queue）
- RAG 轻量组件访问（parser_router, splitter）
- 配置驱动的工厂方法（存储后端、任务队列选择逻辑）
- 错误处理（不支持的配置值）
"""

import os
import tempfile

import pytest

from app.config.settings import Settings
from app.core.container import Container
from app.core.security import SecurityManager
from app.core.storage import LocalFileStorage
from app.core.task_queue.huey_queue import HueyTaskQueue
from app.rag.splitters import FixedSizeSplitter


# ════════════════════════════════════════════════════════════
# 测试夹具
# ════════════════════════════════════════════════════════════


@pytest.fixture(scope="function")
def sqlite_db_path() -> str:
    """创建临时 SQLite 数据库文件路径，测试结束后清理"""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="rag_test_container_")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def test_settings(sqlite_db_path: str) -> Settings:
    """返回测试用配置"""
    return Settings(
        DATABASE_URL=f"sqlite+aiosqlite:///{sqlite_db_path}",
        DATABASE_ECHO=False,
        JWT_SECRET_KEY="test-secret-key",
        JWT_ALGORITHM="HS256",
        STORAGE_BACKEND="local",
        STORAGE_LOCAL_PATH="./test_uploads",
        TASK_QUEUE_BACKEND="huey",
        SPLITTER_TYPE="fixed",
        SPLITTER_CHUNK_SIZE=512,
        SPLITTER_CHUNK_OVERLAP=64,
    )


@pytest.fixture
async def container(test_settings: Settings) -> Container:
    """返回初始化后的 Container 实例"""
    c = Container(test_settings)
    await c.initialize()
    yield c
    await c.close()


# ════════════════════════════════════════════════════════════
# 生命周期
# ════════════════════════════════════════════════════════════


class TestLifecycle:
    """Container 生命周期测试"""

    async def test_initialize_sets_initialized(self, test_settings: Settings):
        """initialize() 后 initialized 应为 True"""
        container = Container(test_settings)
        assert container.initialized is False
        await container.initialize()
        assert container.initialized is True
        await container.close()

    async def test_close_resets_initialized(self, container: Container):
        """close() 后 initialized 应为 False"""
        assert container.initialized is True
        await container.close()
        assert container.initialized is False

    async def test_double_initialize_is_idempotent(
        self, test_settings: Settings
    ):
        """重复 initialize() 应幂等"""
        container = Container(test_settings)
        await container.initialize()
        await container.initialize()  # 第二次不应报错
        assert container.initialized is True
        await container.close()

    async def test_close_without_initialize(self, test_settings: Settings):
        """未初始化直接 close() 不应报错"""
        container = Container(test_settings)
        await container.close()  # 不应抛出异常

    def test_create_without_initialize(self, test_settings: Settings):
        """创建 Container 实例后不应自动初始化"""
        container = Container(test_settings)
        assert container.initialized is False


# ════════════════════════════════════════════════════════════
# Core 基础设施
# ════════════════════════════════════════════════════════════


class TestCoreInfrastructure:
    """Core 基础设施组件测试"""

    async def test_security_property(self, container: Container):
        """security 属性应返回 SecurityManager 实例"""
        security = container.security
        assert isinstance(security, SecurityManager)
        # 验证功能正常
        token = security.create_access_token("test-user", "admin")
        payload = security.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user"
        assert payload["role"] == "admin"

    async def test_db_property(self, container: Container):
        """db 属性应返回 DatabaseManager 实例"""
        from app.core.database import DatabaseManager
        assert isinstance(container.db, DatabaseManager)

    async def test_storage_property_default(self, container: Container):
        """storage 属性应返回 LocalFileStorage 实例"""
        storage = container.storage
        assert isinstance(storage, LocalFileStorage)

    async def test_task_queue_property_default(self, container: Container):
        """task_queue 属性应返回 HueyTaskQueue 实例"""
        queue = container.task_queue
        assert isinstance(queue, HueyTaskQueue)


# ════════════════════════════════════════════════════════════
# 懒加载验证
# ════════════════════════════════════════════════════════════


class TestLazyLoading:
    """懒加载验证"""

    async def test_db_access_before_init_raises(self, test_settings: Settings):
        """初始化前访问 db 属性应抛出 RuntimeError"""
        container = Container(test_settings)
        with pytest.raises(RuntimeError, match="尚未初始化"):
            _ = container.db

    async def test_security_not_initialized_before_first_access(
        self, test_settings: Settings
    ):
        """security 在首次访问前 _security 应为 None"""
        container = Container(test_settings)
        assert container._security is None
        _ = container.security
        assert container._security is not None

    async def test_storage_not_initialized_before_first_access(
        self, test_settings: Settings
    ):
        """storage 在首次访问前 _storage 应为 None"""
        container = Container(test_settings)
        assert container._storage is None
        _ = container.storage
        assert container._storage is not None

    async def test_security_cached_after_first_access(
        self, container: Container
    ):
        """security 首次访问后应被缓存"""
        first = container.security
        second = container.security
        assert first is second


# ════════════════════════════════════════════════════════════
# RAG 轻量组件
# ════════════════════════════════════════════════════════════


class TestRAGComponents:
    """RAG 组件测试（仅测试可独立运行的轻量组件）"""

    async def test_parser_router(self, container: Container):
        """parser_router 应返回已注册默认解析器的路由"""
        router = container.parser_router
        from app.rag.parsers import ParserRouter
        assert isinstance(router, ParserRouter)
        # 验证已注册默认解析器
        for ext in [".txt", ".md", ".pdf", ".docx"]:
            parser = router.get_parser(ext)
            assert parser is not None, f"{ext} 解析器未注册"

    async def test_splitter_default(self, container: Container):
        """splitter 应返回 FixedSizeSplitter 实例"""
        splitter = container.splitter
        assert isinstance(splitter, FixedSizeSplitter)
        assert splitter._chunk_size == 512
        assert splitter._chunk_overlap == 64

    async def test_splitter_not_implemented_types(
        self, test_settings: Settings
    ):
        """不支持的 splitter 类型应抛出对应错误"""
        container = Container(test_settings)
        await container.initialize()

        # markdown 类型（预留）
        container._settings.SPLITTER_TYPE = "markdown"
        with pytest.raises(NotImplementedError, match="尚未实现"):
            _ = container.splitter

        # semantic 类型（预留）
        container._settings.SPLITTER_TYPE = "semantic"
        with pytest.raises(NotImplementedError, match="尚未实现"):
            _ = container.splitter

        await container.close()

    def test_unsupported_splitter_raises(self, test_settings: Settings):
        """不支持的 SPLITTER_TYPE 应抛出 ValueError"""
        container = Container(test_settings)
        container._settings.SPLITTER_TYPE = "invalid"
        with pytest.raises(ValueError, match="不支持的 SPLITTER_TYPE"):
            _ = container.splitter


# ════════════════════════════════════════════════════════════
# 工厂方法
# ════════════════════════════════════════════════════════════


class TestStorageFactory:
    """存储后端工厂方法测试"""

    async def test_local_storage(self, test_settings: Settings):
        """STORAGE_BACKEND=local 应返回 LocalFileStorage"""
        container = Container(test_settings)
        await container.initialize()

        container._settings.STORAGE_BACKEND = "local"
        storage = container._create_storage()
        assert isinstance(storage, LocalFileStorage)
        await container.close()

    def test_unsupported_storage_raises(self, test_settings: Settings):
        """不支持的存储后端应抛出 ValueError"""
        container = Container(test_settings)
        container._settings.STORAGE_BACKEND = "invalid_backend"
        with pytest.raises(ValueError, match="不支持的 STORAGE_BACKEND"):
            container._create_storage()

    def test_s3_storage_not_implemented(self, test_settings: Settings):
        """s3 存储后端应抛出 NotImplementedError"""
        container = Container(test_settings)
        container._settings.STORAGE_BACKEND = "s3"
        with pytest.raises(NotImplementedError, match="尚未实现"):
            container._create_storage()


class TestTaskQueueFactory:
    """任务队列工厂方法测试"""

    def test_huey_task_queue(self, test_settings: Settings):
        """TASK_QUEUE_BACKEND=huey 应返回 HueyTaskQueue"""
        container = Container(test_settings)
        queue = container._create_task_queue()
        assert isinstance(queue, HueyTaskQueue)

    def test_unsupported_queue_raises(self, test_settings: Settings):
        """不支持的任务队列后端应抛出 ValueError"""
        container = Container(test_settings)
        container._settings.TASK_QUEUE_BACKEND = "invalid"
        with pytest.raises(ValueError, match="不支持的任务队列后端"):
            container._create_task_queue()

    def test_celery_not_implemented(self, test_settings: Settings):
        """celery 任务队列应抛出 NotImplementedError"""
        container = Container(test_settings)
        container._settings.TASK_QUEUE_BACKEND = "celery"
        with pytest.raises(NotImplementedError, match="尚未实现"):
            container._create_task_queue()

    def test_arq_not_implemented(self, test_settings: Settings):
        """arq 任务队列应抛出 NotImplementedError"""
        container = Container(test_settings)
        container._settings.TASK_QUEUE_BACKEND = "arq"
        with pytest.raises(NotImplementedError, match="尚未实现"):
            container._create_task_queue()


class TestVectorStoreFactory:
    """向量存储工厂方法测试"""

    def test_chromadb_default(self, test_settings: Settings):
        """VECTOR_STORE_BACKEND=chromadb 应返回 ChromaDBStore"""
        container = Container(test_settings)
        container._settings.VECTOR_STORE_BACKEND = "chromadb"
        store = container._create_vector_store()
        from app.rag.vector_stores.chromadb_store import ChromaDBStore
        assert isinstance(store, ChromaDBStore)

    def test_unsupported_vector_store_raises(self, test_settings: Settings):
        """不支持的向量存储后端应抛出 ValueError"""
        container = Container(test_settings)
        container._settings.VECTOR_STORE_BACKEND = "invalid"
        with pytest.raises(ValueError, match="不支持的 VECTOR_STORE_BACKEND"):
            container._create_vector_store()

    def test_faiss_not_implemented(self, test_settings: Settings):
        """faiss 向量存储应抛出 NotImplementedError"""
        container = Container(test_settings)
        container._settings.VECTOR_STORE_BACKEND = "faiss"
        with pytest.raises(NotImplementedError):
            container._create_vector_store()

    def test_milvus_not_implemented(self, test_settings: Settings):
        """milvus 向量存储应抛出 NotImplementedError"""
        container = Container(test_settings)
        container._settings.VECTOR_STORE_BACKEND = "milvus"
        with pytest.raises(NotImplementedError):
            container._create_vector_store()

    def test_pgvector_not_implemented(self, test_settings: Settings):
        """pgvector 向量存储应抛出 NotImplementedError"""
        container = Container(test_settings)
        container._settings.VECTOR_STORE_BACKEND = "pgvector"
        with pytest.raises(NotImplementedError):
            container._create_vector_store()


# ════════════════════════════════════════════════════════════
# 业务服务
# ════════════════════════════════════════════════════════════


class TestServices:
    """业务服务组件测试"""

    async def test_user_service(self, container: Container):
        """user_service 应可访问"""
        svc = container.user_service
        from app.services.user_service import UserService
        assert isinstance(svc, UserService)

    async def test_dataset_service(self, container: Container):
        """dataset_service 应可访问"""
        svc = container.dataset_service
        from app.services.dataset_service import DatasetService
        assert isinstance(svc, DatasetService)

    async def test_admin_service(self, container: Container):
        """admin_service 应可访问"""
        svc = container.admin_service
        from app.services.admin_service import AdminService
        assert isinstance(svc, AdminService)


# ════════════════════════════════════════════════════════════
# 静态工厂方法
# ════════════════════════════════════════════════════════════


class TestStaticFactory:
    """Container 静态工厂方法测试"""

    async def test_get_returns_container(self):
        """Container.get() 应返回 Container 实例"""
        Container.clear_container()
        c = await Container.get()
        assert isinstance(c, Container)
        assert c.initialized is True
        await c.close()
        Container.clear_container()

    async def test_set_container(self, test_settings: Settings):
        """set_container() 应设置全局容器"""
        container = Container(test_settings)
        await container.initialize()

        Container.clear_container()
        Container.set_container(container)

        retrieved = await Container.get()
        assert retrieved is container
        await container.close()
        Container.clear_container()

    async def test_clear_container(self, test_settings: Settings):
        """clear_container() 应清除全局容器"""
        container = Container(test_settings)
        await container.initialize()
        Container.set_container(container)
        Container.clear_container()

        # 清除后 get() 应创建新实例
        new_container = await Container.get()
        assert new_container is not container
        await new_container.close()
        Container.clear_container()
