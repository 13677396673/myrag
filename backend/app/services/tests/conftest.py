"""用户服务 + 数据集服务 + 文档服务测试夹具"""

import os
import tempfile

import pytest

from unittest.mock import AsyncMock, MagicMock

from app.config.settings import Settings
from app.core.database import DatabaseManager
from app.core.security import SecurityManager
from app.services.conversation_service import ConversationService
from app.services.dataset_service import DatasetService
from app.services.document_service import DocumentService
from app.services.user_service import UserService


@pytest.fixture(scope="function")
def sqlite_db_path() -> str:
    """创建临时 SQLite 数据库文件路径，测试结束后清理"""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="rag_test_svc_")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def settings(sqlite_db_path: str) -> Settings:
    """返回指向临时 SQLite 文件的配置"""
    return Settings(
        DATABASE_URL=f"sqlite+aiosqlite:///{sqlite_db_path}",
        DATABASE_ECHO=False,
        JWT_SECRET_KEY="test-secret",
        JWT_ALGORITHM="HS256",
    )


@pytest.fixture(scope="function")
async def db_manager(settings: Settings) -> DatabaseManager:
    """创建并初始化数据库，建表后返回"""
    db = DatabaseManager(settings)
    await db.initialize()
    await db.create_tables()
    yield db
    await db.close()


@pytest.fixture(scope="function")
def security(settings: Settings) -> SecurityManager:
    """返回测试用的 SecurityManager"""
    return SecurityManager(settings)


@pytest.fixture(scope="function")
def user_service(
    db_manager: DatabaseManager,
    security: SecurityManager,
) -> UserService:
    """返回测试用的 UserService 实例"""
    return UserService(db=db_manager, security=security)


@pytest.fixture(scope="function")
def dataset_service(db_manager: DatabaseManager) -> DatasetService:
    """返回测试用的 DatasetService 实例"""
    return DatasetService(db=db_manager)


@pytest.fixture(scope="function")
async def sample_user(user_service: UserService) -> dict:
    """预先创建一个测试用户，返回注册信息和响应"""
    from app.schemas.user import UserRegisterRequest

    request = UserRegisterRequest(
        username="testuser",
        email="test@example.com",
        password="secure123",
    )
    user = await user_service.register(request)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "password": "secure123",
        "role": user.role,
        "is_active": user.is_active,
        "response": user,
    }


@pytest.fixture(scope="function")
async def another_user(user_service: UserService) -> dict:
    """创建另一个测试用户，用于验证用户隔离"""
    from app.schemas.user import UserRegisterRequest

    request = UserRegisterRequest(
        username="otheruser",
        email="other@example.com",
        password="pass456",
    )
    user = await user_service.register(request)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "password": "pass456",
    }


@pytest.fixture(scope="function")
async def sample_dataset(
    dataset_service: DatasetService, sample_user: dict
):
    """预先创建一个测试数据集，返回 DatasetResponse"""
    from app.schemas.dataset import DatasetCreateRequest

    request = DatasetCreateRequest(
        name="测试数据集",
        description="这是一个测试数据集",
    )
    return await dataset_service.create(request, user_id=sample_user["id"])


# ════════════════════════════════════════════════════════════
# 文档服务 Mock 依赖
# ════════════════════════════════════════════════════════════


@pytest.fixture(scope="function")
def mock_storage() -> MagicMock:
    """返回模拟的 FileStorageBackend"""
    storage = MagicMock(spec=["save", "read", "delete", "exists"])
    storage.save = AsyncMock(return_value="/mock/path/test.txt")
    storage.read = AsyncMock(return_value=b"mock content")
    storage.delete = AsyncMock(return_value=True)
    storage.exists = AsyncMock(return_value=True)
    return storage


@pytest.fixture(scope="function")
def mock_task_queue() -> MagicMock:
    """返回模拟的 TaskQueueBackend"""
    queue = MagicMock(spec=["register_task", "enqueue", "enqueue_with_delay"])
    queue.enqueue = MagicMock(return_value="task-id-123")
    queue.enqueue_with_delay = MagicMock(return_value="task-id-456")
    return queue


@pytest.fixture(scope="function")
def mock_pipeline() -> MagicMock:
    """返回模拟的 DocumentPipeline"""
    pipeline = MagicMock(spec=["process_document"])
    pipeline.process_document = MagicMock(return_value=10)
    return pipeline


@pytest.fixture(scope="function")
def document_service(
    db_manager: DatabaseManager,
    mock_storage: MagicMock,
    mock_task_queue: MagicMock,
    mock_pipeline: MagicMock,
) -> DocumentService:
    """返回测试用的 DocumentService 实例"""
    return DocumentService(
        db=db_manager,
        storage=mock_storage,
        task_queue=mock_task_queue,
        pipeline=mock_pipeline,
    )


@pytest.fixture(scope="function")
async def sample_document(
    document_service: DocumentService,
    sample_user: dict,
    sample_dataset,
):
    """预先创建一个测试文档，返回 DocumentResponse"""
    return await document_service.upload_document(
        user_id=sample_user["id"],
        dataset_id=sample_dataset.id,
        filename="test_document.pdf",
        content=b"%PDF-1.4 mock pdf content",
    )


# ════════════════════════════════════════════════════════════
# 对话服务 Mock 依赖
# ════════════════════════════════════════════════════════════


@pytest.fixture(scope="function")
def mock_rag_engine() -> MagicMock:
    """返回模拟的 RAGEngine"""
    engine = MagicMock(spec=["query", "query_stream"])
    engine.query = AsyncMock(
        return_value={"answer": "测试回答", "sources": []}
    )
    return engine


@pytest.fixture(scope="function")
def conversation_service(
    db_manager: DatabaseManager,
    mock_rag_engine: MagicMock,
) -> ConversationService:
    """返回测试用的 ConversationService 实例"""
    return ConversationService(db=db_manager, rag_engine=mock_rag_engine)


@pytest.fixture(scope="function")
async def sample_conversation(
    conversation_service: ConversationService,
    sample_user: dict,
):
    """预先创建一个测试对话，返回 ConversationResponse"""
    from app.schemas.conversation import ConversationCreateRequest

    request = ConversationCreateRequest(
        title="测试对话",
        dataset_id=None,
    )
    return await conversation_service.create_conversation(
        request, user_id=sample_user["id"]
    )

