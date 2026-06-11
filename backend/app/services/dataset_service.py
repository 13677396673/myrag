"""数据集服务 — 数据集的 CRUD 与用户隔离

DatasetService 封装了所有与数据集相关的业务逻辑：
- 创建、查询、更新、删除数据集
- 用户隔离：用户只能操作自己的数据集
- 删除数据集时级联删除关联文档

依赖:
    - DatabaseManager（异步数据库会话）
"""

from typing import List, Optional, Tuple

from sqlalchemy import func, select

from app.core.database import DatabaseManager
from app.core.exceptions import RagError
from app.models.dataset import Dataset
from app.models.document import Document
from app.schemas.dataset import (
    DatasetCreateRequest,
    DatasetResponse,
    DatasetUpdateRequest,
)


# ════════════════════════════════════════════════════════════
# 业务异常
# ════════════════════════════════════════════════════════════


class DatasetServiceError(RagError):
    """数据集服务相关错误的基类"""

    def __init__(
        self,
        code: str = "dataset_service_error",
        message: str = "数据集服务错误",
        detail: object = None,
    ) -> None:
        super().__init__(code=code, message=message, detail=detail)


class DatasetNotFound(DatasetServiceError):
    """数据集不存在"""

    def __init__(self, dataset_id: str) -> None:
        super().__init__(
            code="dataset_not_found",
            message="数据集不存在",
            detail={"dataset_id": dataset_id},
        )


class DatasetPermissionDenied(DatasetServiceError):
    """无权访问该数据集"""

    def __init__(self, dataset_id: str) -> None:
        super().__init__(
            code="dataset_permission_denied",
            message="无权访问该数据集",
            detail={"dataset_id": dataset_id},
        )


# ════════════════════════════════════════════════════════════
# 数据集服务
# ════════════════════════════════════════════════════════════


class DatasetService:
    """数据集服务

    提供数据集的 CRUD 操作，所有操作均校验用户身份：
    - 用户只能查看/修改/删除自己的数据集
    - 删除数据集时级联删除关联的文档

    用法::

        service = DatasetService(db_manager)
        ds = await service.create(request, user_id="...")
        datasets, total = await service.list_datasets(user_id="...")
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ── 创建 ──────────────────────────────────────────────────

    async def create(
        self, request: DatasetCreateRequest, user_id: str
    ) -> DatasetResponse:
        """创建数据集

        流程:
            1. 创建 Dataset 记录
            2. 返回包含文档计数的响应（新数据集文档数为 0）
        """
        async with self._db.get_session() as session:
            dataset = Dataset(
                name=request.name,
                description=request.description,
                user_id=user_id,
            )
            session.add(dataset)
            await session.commit()
            await session.refresh(dataset)

            return self._to_response(dataset, document_count=0)

    # ── 查询单个 ──────────────────────────────────────────────

    async def get_dataset(
        self, dataset_id: str, user_id: str
    ) -> DatasetResponse:
        """根据 ID 获取数据集（含用户隔离检查）

        异常:
            DatasetNotFound — 数据集不存在
            DatasetPermissionDenied — 无权访问
        """
        async with self._db.get_session() as session:
            dataset = await session.get(Dataset, dataset_id)
            if dataset is None:
                raise DatasetNotFound(dataset_id)

            if dataset.user_id != user_id:
                raise DatasetPermissionDenied(dataset_id)

            document_count = await self._count_documents(
                session, dataset_id
            )

            return self._to_response(dataset, document_count)

    # ── 列表（分页） ──────────────────────────────────────────

    async def list_datasets(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[DatasetResponse], int]:
        """获取用户的数据集列表（分页），按创建时间倒序

        返回:
            (数据集列表, 总记录数)
        """
        async with self._db.get_session() as session:
            # 总数
            count_result = await session.execute(
                select(func.count(Dataset.id)).where(
                    Dataset.user_id == user_id
                )
            )
            total: int = count_result.scalar() or 0

            if total == 0:
                return [], 0

            # 分页查询
            offset = (page - 1) * page_size
            result = await session.execute(
                select(Dataset)
                .where(Dataset.user_id == user_id)
                .order_by(Dataset.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            datasets = result.scalars().all()

            # 批量查询文档计数（避免 N+1）
            doc_count_map = await self._batch_count_documents(
                session, [d.id for d in datasets]
            )

            return [
                self._to_response(d, doc_count_map.get(d.id, 0))
                for d in datasets
            ], total

    # ── 更新 ──────────────────────────────────────────────────

    async def update_dataset(
        self,
        dataset_id: str,
        request: DatasetUpdateRequest,
        user_id: str,
    ) -> DatasetResponse:
        """更新数据集信息

        异常:
            DatasetNotFound — 数据集不存在
            DatasetPermissionDenied — 无权修改
        """
        async with self._db.get_session() as session:
            dataset = await session.get(Dataset, dataset_id)
            if dataset is None:
                raise DatasetNotFound(dataset_id)

            if dataset.user_id != user_id:
                raise DatasetPermissionDenied(dataset_id)

            if request.name is not None:
                dataset.name = request.name
            if request.description is not None:
                dataset.description = request.description

            await session.commit()
            await session.refresh(dataset)

            document_count = await self._count_documents(
                session, dataset_id
            )

            return self._to_response(dataset, document_count)

    # ── 删除 ──────────────────────────────────────────────────

    async def delete_dataset(
        self, dataset_id: str, user_id: str
    ) -> None:
        """删除数据集（级联删除关联文档和切片）

        异常:
            DatasetNotFound — 数据集不存在
            DatasetPermissionDenied — 无权删除
        """
        async with self._db.get_session() as session:
            dataset = await session.get(Dataset, dataset_id)
            if dataset is None:
                raise DatasetNotFound(dataset_id)

            if dataset.user_id != user_id:
                raise DatasetPermissionDenied(dataset_id)

            await session.delete(dataset)
            await session.commit()

    # ── 内部辅助 ──────────────────────────────────────────────

    @staticmethod
    def _to_response(
        dataset: Dataset, document_count: int = 0
    ) -> DatasetResponse:
        """将 Dataset ORM 对象转换为 DatasetResponse Pydantic 模式"""
        return DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            document_count=document_count,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )

    @staticmethod
    async def _count_documents(session, dataset_id: str) -> int:
        """统计指定数据集中的文档数量"""
        result = await session.execute(
            select(func.count(Document.id)).where(
                Document.dataset_id == dataset_id
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def _batch_count_documents(
        session, dataset_ids: List[str]
    ) -> dict:
        """批量统计多个数据集中的文档数量，返回 {dataset_id: count}"""
        if not dataset_ids:
            return {}

        result = await session.execute(
            select(
                Document.dataset_id,
                func.count(Document.id),
            )
            .where(Document.dataset_id.in_(dataset_ids))
            .group_by(Document.dataset_id)
        )
        return dict(result.fetchall())
