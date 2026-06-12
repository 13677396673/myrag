"""依赖注入容器 — Container

集中管理所有系统组件的创建、组合和生命周期，通过配置驱动组件选择。
所有 RAG 组件和业务服务均通过 ``@property`` 懒加载，按需初始化。

用法::

    container = Container(settings)
    await container.initialize()

    # 通过属性访问组件（懒加载）
    user = await container.user_service.get_user_by_id("...")
    stats = await container.admin_service.get_stats()

    # 使用完毕后释放资源
    await container.close()
"""

from typing import Optional

from app.config.settings import Settings
from app.core.database import DatabaseManager
from app.core.exceptions import RagError
from app.core.security import SecurityManager
from app.core.storage import FileStorageBackend, LocalFileStorage
from app.core.task_queue import TaskQueueBackend
from app.core.task_queue.huey_queue import HueyTaskQueue
from app.rag.embeddings import BGESmallEmbedding, DeepSeekEmbedding, OpenAIEmbedding
from app.rag.embeddings import create_embedding as _create_embedding
from app.rag.llms import create_llm as _create_llm
from app.rag.parsers import ParserRouter, register_default_parsers
from app.rag.pipeline import DocumentPipeline
from app.rag.rag_engine import RAGEngine
from app.rag.retrievers import create_retriever as _create_retriever
from app.rag.splitters import FixedSizeSplitter
from app.rag.vector_stores import ChromaDBStore
from app.services.admin_service import AdminService
from app.services.conversation_service import ConversationService
from app.services.dataset_service import DatasetService
from app.services.document_service import DocumentService
from app.services.user_service import UserService


class Container:
    """应用依赖注入容器

    集中管理所有系统组件的创建、组合和生命周期。所有组件通过 ``@property``
    懒加载，确保按需初始化，避免启动时不必要的资源消耗。

    使用 ``initialize()`` / ``close()`` 管理 DatabaseManager 等需要
    显式初始化和清理的资源。

    配置驱动的组件选择：
        - 存储后端：``STORAGE_BACKEND`` → local / s3
        - 任务队列：``TASK_QUEUE_BACKEND`` → huey / celery / arq
        - Embedding：``EMBEDDING_BACKEND`` → bge-small / openai / deepseek
        - LLM：``LLM_BACKEND`` → deepseek / openai / ollama
        - 向量存储：``VECTOR_STORE_BACKEND`` → chromadb / faiss / milvus / pgvector
        - 检索器：``RETRIEVAL_MODE`` → vector / hybrid
        - 切片器：``SPLITTER_TYPE`` → fixed / markdown / semantic
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._initialized = False

        # ── Core 基础设施（惰性引用） ──
        self._database: Optional[DatabaseManager] = None
        self._security: Optional[SecurityManager] = None
        self._storage: Optional[FileStorageBackend] = None
        self._task_queue: Optional[TaskQueueBackend] = None

        # ── RAG 组件（惰性引用） ──
        self._parser_router: Optional[ParserRouter] = None
        self._splitter: Optional[FixedSizeSplitter] = None
        self._embedding: Optional[object] = None
        self._vector_store: Optional[object] = None
        self._llm: Optional[object] = None
        self._retriever: Optional[object] = None
        self._pipeline: Optional[DocumentPipeline] = None
        self._rag_engine: Optional[RAGEngine] = None

        # ── 业务服务（惰性引用） ──
        self._user_service: Optional[UserService] = None
        self._dataset_service: Optional[DatasetService] = None
        self._document_service: Optional[DocumentService] = None
        self._conversation_service: Optional[ConversationService] = None
        self._admin_service: Optional[AdminService] = None

    # ════════════════════════════════════════════════════════════
    # 生命周期管理
    # ════════════════════════════════════════════════════════════

    async def initialize(self) -> None:
        """初始化基础设施组件

        执行 DatabaseManager 的异步初始化（创建引擎和连接池）和建表。
        此方法应在应用启动时调用一次。
        """
        if self._initialized:
            return

        # Database 需要异步初始化
        self._database = DatabaseManager(self._settings)
        await self._database.initialize()
        await self._database.create_tables()

        self._initialized = True

    async def close(self) -> None:
        """释放所有资源

        关闭数据库连接池等需要显式清理的资源。
        此方法应在应用关闭时调用。
        """
        if self._database is not None:
            await self._database.close()
            self._database = None
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """容器是否已完成初始化"""
        return self._initialized

    # ════════════════════════════════════════════════════════════
    # Core 基础设施
    # ════════════════════════════════════════════════════════════

    @property
    def db(self) -> DatabaseManager:
        """数据库管理器

        需要在调用前执行 ``initialize()``。
        """
        if self._database is None:
            raise RuntimeError(
                "Container 尚未初始化，请先调用 await container.initialize()"
            )
        return self._database

    @property
    def security(self) -> SecurityManager:
        """安全管理器（密码哈希 + JWT）"""
        if self._security is None:
            self._security = SecurityManager(self._settings)
        return self._security

    @property
    def storage(self) -> FileStorageBackend:
        """文件存储后端（由配置驱动）"""
        if self._storage is None:
            self._storage = self._create_storage()
        return self._storage

    @property
    def task_queue(self) -> TaskQueueBackend:
        """任务队列后端（由配置驱动）"""
        if self._task_queue is None:
            self._task_queue = self._create_task_queue()
        return self._task_queue

    # ════════════════════════════════════════════════════════════
    # RAG 组件（懒加载 @property）
    # ════════════════════════════════════════════════════════════

    @property
    def parser_router(self) -> ParserRouter:
        """文档解析器路由（已注册所有默认解析器）"""
        if self._parser_router is None:
            router = ParserRouter()
            register_default_parsers(router)
            self._parser_router = router
        return self._parser_router

    @property
    def splitter(self) -> FixedSizeSplitter:
        """文本切片器（从配置读取参数）

        支持的切片器类型：
            - ``fixed`` → FixedSizeSplitter
            - ``markdown`` → 预留，抛出 NotImplementedError
            - ``semantic`` → 预留，抛出 NotImplementedError
        """
        if self._splitter is None:
            splitter_type = self._settings.SPLITTER_TYPE
            chunk_size = self._settings.SPLITTER_CHUNK_SIZE
            chunk_overlap = self._settings.SPLITTER_CHUNK_OVERLAP

            if splitter_type == "fixed":
                self._splitter = FixedSizeSplitter(
                    chunk_size=chunk_size, chunk_overlap=chunk_overlap
                )
            elif splitter_type == "markdown":
                raise NotImplementedError(
                    "Markdown 结构切片器尚未实现（预留中）"
                )
            elif splitter_type == "semantic":
                raise NotImplementedError(
                    "语义边界切片器尚未实现（预留中）"
                )
            else:
                msg = f"不支持的 SPLITTER_TYPE: {splitter_type!r}"
                msg += "，可选值: fixed, markdown, semantic"
                raise ValueError(msg)
        return self._splitter

    @property
    def embedding(self) -> object:
        """Embedding 后端（由配置驱动）"""
        if self._embedding is None:
            self._embedding = _create_embedding(self._settings)
        return self._embedding

    @property
    def vector_store(self) -> object:
        """向量存储后端（由配置驱动）"""
        if self._vector_store is None:
            self._vector_store = self._create_vector_store()
        return self._vector_store

    @property
    def llm(self) -> object:
        """LLM 后端（由配置驱动）"""
        if self._llm is None:
            self._llm = _create_llm(self._settings)
        return self._llm

    @property
    def retriever(self) -> object:
        """检索器（组合 embedding + vector_store）"""
        if self._retriever is None:
            self._retriever = _create_retriever(
                self._settings, self.embedding, self.vector_store
            )
        return self._retriever

    @property
    def pipeline(self) -> DocumentPipeline:
        """文档处理管道

        组合 parser_router + splitter + embedding + vector_store。
        """
        if self._pipeline is None:
            self._pipeline = DocumentPipeline(
                parser_router=self.parser_router,
                splitter=self.splitter,
                embedding=self.embedding,
                vector_store=self.vector_store,
            )
        return self._pipeline

    @property
    def rag_engine(self) -> RAGEngine:
        """RAG 问答引擎

        组合 retriever + llm。
        """
        if self._rag_engine is None:
            self._rag_engine = RAGEngine(
                retriever=self.retriever,
                llm=self.llm,
            )
        return self._rag_engine

    # ════════════════════════════════════════════════════════════
    # 业务服务（懒加载 @property）
    # ════════════════════════════════════════════════════════════

    @property
    def user_service(self) -> UserService:
        """用户服务"""
        if self._user_service is None:
            self._user_service = UserService(db=self.db, security=self.security)
        return self._user_service

    @property
    def dataset_service(self) -> DatasetService:
        """数据集服务"""
        if self._dataset_service is None:
            self._dataset_service = DatasetService(db=self.db)
        return self._dataset_service

    @property
    def document_service(self) -> DocumentService:
        """文档服务"""
        if self._document_service is None:
            self._document_service = DocumentService(
                db=self.db,
                storage=self.storage,
                task_queue=self.task_queue,
                pipeline=self.pipeline,
            )
        return self._document_service

    @property
    def conversation_service(self) -> ConversationService:
        """对话服务"""
        if self._conversation_service is None:
            self._conversation_service = ConversationService(
                db=self.db, rag_engine=self.rag_engine
            )
        return self._conversation_service

    @property
    def admin_service(self) -> AdminService:
        """管理后台服务"""
        if self._admin_service is None:
            self._admin_service = AdminService(db=self.db)
        return self._admin_service

    # ════════════════════════════════════════════════════════════
    # 工厂方法
    # ════════════════════════════════════════════════════════════

    @staticmethod
    async def get() -> "Container":
        """FastAPI Depends 工厂方法

        返回全局单例容器。在 ``main.py`` 中通过 ``set_container()``
        或首次调用时自动创建。

        用法::

            from fastapi import Depends
            from app.core.container import Container

            @router.get("/users/me")
            async def get_user(container: Container = Depends(Container.get)):
                ...
        """
        from app.config.settings import settings as global_settings

        if not hasattr(Container, "_global_container"):
            container = Container(global_settings)
            await container.initialize()
            Container._global_container = container
        return Container._global_container

    @staticmethod
    def set_container(container: "Container") -> None:
        """设置全局容器实例（供测试覆盖或 main.py 使用）"""
        Container._global_container = container

    @staticmethod
    def clear_container() -> None:
        """清除全局容器实例（主要用于测试清理）"""
        if hasattr(Container, "_global_container"):
            del Container._global_container

    # ════════════════════════════════════════════════════════════
    # 内部工厂方法
    # ════════════════════════════════════════════════════════════

    def _create_storage(self) -> FileStorageBackend:
        """根据配置创建文件存储后端

        支持的后端：
            - ``local`` → LocalFileStorage
            - ``s3`` → 预留，抛出 NotImplementedError
        """
        backend = self._settings.STORAGE_BACKEND

        if backend == "local":
            return LocalFileStorage(
                base_path=self._settings.STORAGE_LOCAL_PATH,
            )

        if backend in ("s3", "minio"):
            raise NotImplementedError(
                f"存储后端 {backend!r} 尚未实现（预留中）"
            )

        msg = f"不支持的 STORAGE_BACKEND: {backend!r}，可选值: local, s3, minio"
        raise ValueError(msg)

    def _create_task_queue(self) -> TaskQueueBackend:
        """根据配置创建任务队列后端

        支持的后端：
            - ``huey`` → HueyTaskQueue
            - ``celery`` → 预留，抛出 NotImplementedError
            - ``arq`` → 预留，抛出 NotImplementedError
        """
        backend = self._settings.TASK_QUEUE_BACKEND

        if backend == "huey":
            return HueyTaskQueue()

        if backend in ("celery", "arq"):
            raise NotImplementedError(
                f"任务队列后端 {backend!r} 尚未实现（预留中）"
            )

        msg = f"不支持的任务队列后端: {backend!r}，可选值: huey, celery, arq"
        raise ValueError(msg)

    def _create_vector_store(self) -> object:
        """根据配置创建向量存储后端

        支持的后端：
            - ``chromadb`` → ChromaDBStore
            - ``faiss`` → 预留
            - ``milvus`` → 预留
            - ``pgvector`` → 预留
        """
        backend = self._settings.VECTOR_STORE_BACKEND

        if backend == "chromadb":
            return ChromaDBStore(
                persist_directory=self._settings.VECTOR_STORE_CHROMA_PATH,
            )

        if backend == "faiss":
            raise NotImplementedError(
                "FAISS 向量存储后端尚未实现（预留中）"
            )

        if backend == "milvus":
            raise NotImplementedError(
                "Milvus 向量存储后端尚未实现（预留中）"
            )

        if backend == "pgvector":
            raise NotImplementedError(
                "PGVector 向量存储后端尚未实现（预留中）"
            )

        msg = f"不支持的 VECTOR_STORE_BACKEND: {backend!r}"
        msg += f"，可选值: chromadb, faiss, milvus, pgvector"
        raise ValueError(msg)


# 全局容器实例，供 FastAPI Depends 使用
_global_container: Optional[Container] = None
