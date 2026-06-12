"""API 依赖注入 — JWT 鉴权、DI 容器、当前用户获取

提供 FastAPI 依赖注入函数，用于：
- JWT token 验证与当前用户解析
- 管理员权限检查
- 全局服务容器管理
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.settings import Settings, settings as global_settings
from app.core.database import DatabaseManager
from app.core.exceptions import RagError
from app.core.security import SecurityManager
from app.core.storage import FileStorageBackend, LocalFileStorage
from app.core.task_queue import TaskQueueBackend
from app.core.task_queue.huey_queue import HueyTaskQueue
from app.rag.rag_engine import RAGEngine
from app.rag.pipeline import DocumentPipeline
from app.services.admin_service import AdminService
from app.services.conversation_service import ConversationService
from app.services.dataset_service import DatasetService
from app.services.document_service import DocumentService
from app.services.user_service import UserService

# 无 token 时返回 None 而非 403（由依赖函数自行处理）
bearer_scheme = HTTPBearer(auto_error=False)


# ════════════════════════════════════════════════════════════
# DI 容器
# ════════════════════════════════════════════════════════════


class Container:
    """简单依赖注入容器，持有所有服务实例

    用法::

        container = Container(settings)
        await container.init_async()
        # 现在 container.user_service 等可用
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._initialized = False

        # Core 组件（延迟初始化）
        self.db: Optional[DatabaseManager] = None
        self.security: Optional[SecurityManager] = None
        self.storage: Optional[FileStorageBackend] = None
        self.task_queue: Optional[TaskQueueBackend] = None

        # RAG 组件
        self.pipeline: Optional[DocumentPipeline] = None
        self.rag_engine: Optional[RAGEngine] = None

        # 服务
        self.user_service: Optional[UserService] = None
        self.dataset_service: Optional[DatasetService] = None
        self.document_service: Optional[DocumentService] = None
        self.conversation_service: Optional[ConversationService] = None
        self.admin_service: Optional[AdminService] = None

    async def init_async(self) -> None:
        """异步初始化所有组件（建表、连接池等）"""
        if self._initialized:
            return

        # ── Core ──
        self.security = SecurityManager(self._settings)
        self.db = DatabaseManager(self._settings)
        await self.db.initialize()
        await self.db.create_tables()

        # ── 存储后端 ──
        if self._settings.STORAGE_BACKEND == "local":
            self.storage = LocalFileStorage(
                base_path=self._settings.STORAGE_LOCAL_PATH,
            )
        else:
            self.storage = LocalFileStorage(
                base_path=self._settings.STORAGE_LOCAL_PATH,
            )

        # ── 任务队列 ──
        if self._settings.TASK_QUEUE_BACKEND == "huey":
            self.task_queue = HueyTaskQueue()
        else:
            self.task_queue = HueyTaskQueue()

        # ── RAG 组件（简化版，通过 lazy import 避免循环依赖）─
        from app.rag.embeddings.bge_embedding import BGEEmbedding
        from app.rag.llms.deepseek_llm import DeepSeekLLM
        from app.rag.parsers.parser_router import ParserRouter
        from app.rag.retrievers.vector_retriever import VectorRetriever
        from app.rag.splitters.fixed_splitter import FixedSplitter
        from app.rag.vector_stores.chromadb_store import ChromaDBStore

        self.pipeline = DocumentPipeline(
            parser_router=ParserRouter(),
            splitter=FixedSplitter(
                chunk_size=self._settings.SPLITTER_CHUNK_SIZE,
                chunk_overlap=self._settings.SPLITTER_CHUNK_OVERLAP,
            ),
            embedding=BGEEmbedding(
                model_name=self._settings.EMBEDDING_BGE_MODEL,
                device=self._settings.EMBEDDING_BGE_DEVICE,
            ),
            vector_store=ChromaDBStore(
                persist_dir=self._settings.VECTOR_STORE_CHROMA_PATH,
            ),
        )

        self.rag_engine = RAGEngine(
            retriever=VectorRetriever(
                vector_store=self.pipeline.vector_store,
                embedding=self.pipeline.embedding,
                top_k=self._settings.RETRIEVAL_TOP_K,
            ),
            llm=DeepSeekLLM(
                api_key=self._settings.DEEPSEEK_API_KEY or "",
                model=self._settings.DEEPSEEK_MODEL,
                base_url=self._settings.DEEPSEEK_BASE_URL,
            ),
        )

        # ── 服务 ──
        self.user_service = UserService(db=self.db, security=self.security)
        self.dataset_service = DatasetService(db=self.db)
        self.document_service = DocumentService(
            db=self.db,
            storage=self.storage,
            task_queue=self.task_queue,
            pipeline=self.pipeline,
        )
        self.conversation_service = ConversationService(
            db=self.db,
            rag_engine=self.rag_engine,
        )
        self.admin_service = AdminService(db=self.db)

        self._initialized = True

    async def close(self) -> None:
        """释放所有资源"""
        if self.db is not None:
            await self.db.close()


# 全局容器实例（由 main.py 初始化）
_container: Optional[Container] = None


async def get_container() -> Container:
    """FastAPI 依赖：返回全局 DI 容器

    默认使用全局 ``_container`` 实例；测试可通过
    ``app.dependency_overrides[get_container]`` 覆盖。
    """
    global _container
    if _container is None:
        _container = Container(global_settings)
        await _container.init_async()
    return _container


def set_container(container: Container) -> None:
    """设置全局容器（供 main.py 或测试使用）"""
    global _container
    _container = container


# ════════════════════════════════════════════════════════════
# 鉴权依赖
# ════════════════════════════════════════════════════════════


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    container: Container = Depends(get_container),
) -> str:
    """从 JWT token 中解析当前用户 ID

    流程:
        1. 检查 Bearer token 是否存在
        2. 用 SecurityManager 验证 token 签名和有效期
        3. 从 payload 中提取 ``sub``（用户 ID）

    异常:
        HTTPException(401) — token 缺失、无效、过期
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if container.security is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="安全组件未初始化",
        )

    payload = container.security.verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub", "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def require_admin(
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
) -> str:
    """要求当前用户为管理员

    通过 UserService 查询用户角色，若非 admin 则拒绝。

    异常:
        HTTPException(403) — 非管理员用户
    """
    if container.user_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户服务未初始化",
        )

    user = await container.user_service.get_user_by_id(user_id)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    return user_id
