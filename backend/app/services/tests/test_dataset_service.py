"""数据集服务单元测试

覆盖 DatasetService 的所有公开方法，包括正常流程和异常场景。
重点验证用户隔离：用户只能操作自己的数据集。
"""

import pytest

from app.schemas.dataset import (
    DatasetCreateRequest,
    DatasetUpdateRequest,
)
from app.services.dataset_service import (
    DatasetNotFound,
    DatasetPermissionDenied,
    DatasetService,
    DatasetServiceError,
)


# ════════════════════════════════════════════════════════════
# 创建
# ════════════════════════════════════════════════════════════


class TestCreateDataset:
    """创建数据集测试"""

    async def test_create_success(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
    ):
        """正常创建数据集应返回完整信息"""
        request = DatasetCreateRequest(
            name="我的知识库",
            description="用于测试的知识库",
        )
        result = await dataset_service.create(request, user_id=sample_user["id"])

        assert result.name == "我的知识库"
        assert result.description == "用于测试的知识库"
        assert result.document_count == 0
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

    async def test_create_without_description(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
    ):
        """创建数据集时描述为可选"""
        request = DatasetCreateRequest(name="无描述数据集")
        result = await dataset_service.create(request, user_id=sample_user["id"])

        assert result.name == "无描述数据集"
        assert result.description is None
        assert result.document_count == 0


# ════════════════════════════════════════════════════════════
# 查询单个
# ════════════════════════════════════════════════════════════


class TestGetDataset:
    """获取数据集测试"""

    async def test_get_own_dataset(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        sample_dataset,
    ):
        """获取自己的数据集应成功"""
        result = await dataset_service.get_dataset(
            sample_dataset.id, user_id=sample_user["id"]
        )

        assert result.id == sample_dataset.id
        assert result.name == "测试数据集"
        assert result.description == "这是一个测试数据集"

    async def test_get_others_dataset(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        another_user: dict,
        sample_dataset,
    ):
        """获取别人的数据集应抛出 DatasetPermissionDenied"""
        with pytest.raises(DatasetPermissionDenied):
            await dataset_service.get_dataset(
                sample_dataset.id, user_id=another_user["id"]
            )

    async def test_get_nonexistent_dataset(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
    ):
        """不存在的数据集应抛出 DatasetNotFound"""
        with pytest.raises(DatasetNotFound):
            await dataset_service.get_dataset(
                "non-existent-id", user_id=sample_user["id"]
            )


# ════════════════════════════════════════════════════════════
# 列表（分页）
# ════════════════════════════════════════════════════════════


class TestListDatasets:
    """数据集列表测试"""

    async def test_list_empty(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
    ):
        """无数据集时应返回空列表"""
        datasets, total = await dataset_service.list_datasets(
            user_id=sample_user["id"]
        )
        assert len(datasets) == 0
        assert total == 0

    async def test_list_with_data(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        sample_dataset,
    ):
        """有数据集时应返回正确数量"""
        datasets, total = await dataset_service.list_datasets(
            user_id=sample_user["id"]
        )
        assert total == 1
        assert len(datasets) == 1
        assert datasets[0].name == "测试数据集"
        assert datasets[0].document_count == 0

    async def test_list_only_own_datasets(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        another_user: dict,
        sample_dataset,
    ):
        """用户只能看到自己的数据集"""
        # 为另一个用户创建数据集
        req = DatasetCreateRequest(name="别人的数据集")
        await dataset_service.create(req, user_id=another_user["id"])

        # sample_user 应该只能看到自己的 1 个
        datasets, total = await dataset_service.list_datasets(
            user_id=sample_user["id"]
        )
        assert total == 1
        assert datasets[0].name == "测试数据集"

        # another_user 应该看到自己的 1 个
        datasets2, total2 = await dataset_service.list_datasets(
            user_id=another_user["id"]
        )
        assert total2 == 1
        assert datasets2[0].name == "别人的数据集"

    async def test_list_pagination(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
    ):
        """分页参数应正确工作"""
        # 创建 5 个数据集
        for i in range(5):
            req = DatasetCreateRequest(name=f"数据集{i}")
            await dataset_service.create(req, user_id=sample_user["id"])

        # 第一页（每页 3 条）
        datasets, total = await dataset_service.list_datasets(
            user_id=sample_user["id"], page=1, page_size=3
        )
        assert total == 5
        assert len(datasets) == 3

        # 第二页
        datasets2, total2 = await dataset_service.list_datasets(
            user_id=sample_user["id"], page=2, page_size=3
        )
        assert total2 == 5
        assert len(datasets2) == 2

    async def test_list_order(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
    ):
        """列表应按创建时间倒序排列"""
        for i in range(3):
            req = DatasetCreateRequest(name=f"顺序数据集{i}")
            await dataset_service.create(req, user_id=sample_user["id"])

        datasets, total = await dataset_service.list_datasets(
            user_id=sample_user["id"], page_size=10
        )
        assert total == 3
        names = [d.name for d in datasets]
        assert "顺序数据集2" in names
        assert "顺序数据集1" in names
        assert "顺序数据集0" in names


# ════════════════════════════════════════════════════════════
# 更新
# ════════════════════════════════════════════════════════════


class TestUpdateDataset:
    """更新数据集测试"""

    async def test_update_name_and_description(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        sample_dataset,
    ):
        """更新名称和描述应成功"""
        request = DatasetUpdateRequest(
            name="新名称",
            description="新描述",
        )
        result = await dataset_service.update_dataset(
            sample_dataset.id, request, user_id=sample_user["id"]
        )

        assert result.name == "新名称"
        assert result.description == "新描述"

    async def test_update_partial(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        sample_dataset,
    ):
        """仅更新名称时描述应保持不变"""
        # 先确认描述是 "这是一个测试数据集"
        assert sample_dataset.description == "这是一个测试数据集"

        request = DatasetUpdateRequest(name="仅改名称")
        result = await dataset_service.update_dataset(
            sample_dataset.id, request, user_id=sample_user["id"]
        )

        assert result.name == "仅改名称"
        assert result.description == "这是一个测试数据集"  # 保持不变

    async def test_update_others_dataset(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        another_user: dict,
        sample_dataset,
    ):
        """修改别人的数据集应抛出 DatasetPermissionDenied"""
        request = DatasetUpdateRequest(name="想改别人的")
        with pytest.raises(DatasetPermissionDenied):
            await dataset_service.update_dataset(
                sample_dataset.id, request, user_id=another_user["id"]
            )

    async def test_update_nonexistent(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
    ):
        """修改不存在的数据集应抛出 DatasetNotFound"""
        request = DatasetUpdateRequest(name="不存在")
        with pytest.raises(DatasetNotFound):
            await dataset_service.update_dataset(
                "non-existent-id", request, user_id=sample_user["id"]
            )


# ════════════════════════════════════════════════════════════
# 删除
# ════════════════════════════════════════════════════════════


class TestDeleteDataset:
    """删除数据集测试"""

    async def test_delete_own_dataset(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        sample_dataset,
    ):
        """删除自己的数据集应成功"""
        await dataset_service.delete_dataset(
            sample_dataset.id, user_id=sample_user["id"]
        )

        # 验证已被删除
        with pytest.raises(DatasetNotFound):
            await dataset_service.get_dataset(
                sample_dataset.id, user_id=sample_user["id"]
            )

    async def test_delete_others_dataset(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        another_user: dict,
        sample_dataset,
    ):
        """删除别人的数据集应抛出 DatasetPermissionDenied"""
        with pytest.raises(DatasetPermissionDenied):
            await dataset_service.delete_dataset(
                sample_dataset.id, user_id=another_user["id"]
            )

        # 验证数据集仍然存在（sample_user 仍能访问）
        result = await dataset_service.get_dataset(
            sample_dataset.id, user_id=sample_user["id"]
        )
        assert result.id == sample_dataset.id

    async def test_delete_nonexistent(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
    ):
        """删除不存在的数据集应抛出 DatasetNotFound"""
        with pytest.raises(DatasetNotFound):
            await dataset_service.delete_dataset(
                "non-existent-id", user_id=sample_user["id"]
            )


# ════════════════════════════════════════════════════════════
# 级联删除
# ════════════════════════════════════════════════════════════


class TestCascadeDelete:
    """数据集级联删除测试"""

    async def test_delete_cascade_removes_documents(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        sample_dataset,
        db_manager,
    ):
        """删除数据集时应级联删除关联文档"""
        # 创建文档关联到数据集
        from app.models.document import Document

        async with db_manager.get_session() as session:
            doc = Document(
                filename="test.txt",
                file_type="txt",
                file_size=100,
                file_path="/tmp/test.txt",
                dataset_id=sample_dataset.id,
                user_id=sample_user["id"],
            )
            session.add(doc)
            await session.commit()

        # 验证文档存在
        async with db_manager.get_session() as session:
            from sqlalchemy import select, func

            cnt = await session.execute(
                select(func.count(Document.id)).where(
                    Document.dataset_id == sample_dataset.id
                )
            )
            assert cnt.scalar() == 1

        # 删除数据集
        await dataset_service.delete_dataset(
            sample_dataset.id, user_id=sample_user["id"]
        )

        # 验证文档已被级联删除
        async with db_manager.get_session() as session:
            from sqlalchemy import select, func

            cnt = await session.execute(
                select(func.count(Document.id)).where(
                    Document.dataset_id == sample_dataset.id
                )
            )
            assert cnt.scalar() == 0


# ════════════════════════════════════════════════════════════
# document_count 正确性
# ════════════════════════════════════════════════════════════


class TestDocumentCount:
    """文档计数测试"""

    async def test_document_count_on_create(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
    ):
        """新创建的数据集文档数应为 0"""
        request = DatasetCreateRequest(name="计数测试")
        result = await dataset_service.create(request, user_id=sample_user["id"])
        assert result.document_count == 0

    async def test_document_count_on_get(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        sample_dataset,
        db_manager,
    ):
        """获取数据集时 document_count 应正确"""
        from app.models.document import Document
        from sqlalchemy import select

        # 添加 3 个文档
        async with db_manager.get_session() as session:
            for i in range(3):
                doc = Document(
                    filename=f"doc{i}.txt",
                    file_type="txt",
                    file_size=100,
                    file_path=f"/tmp/doc{i}.txt",
                    dataset_id=sample_dataset.id,
                    user_id=sample_user["id"],
                )
                session.add(doc)
            await session.commit()

        result = await dataset_service.get_dataset(
            sample_dataset.id, user_id=sample_user["id"]
        )
        assert result.document_count == 3

    async def test_document_count_in_list(
        self,
        dataset_service: DatasetService,
        sample_user: dict,
        sample_dataset,
        db_manager,
    ):
        """列表中的 document_count 应正确"""
        from app.models.document import Document

        async with db_manager.get_session() as session:
            doc = Document(
                filename="doc.txt",
                file_type="txt",
                file_size=100,
                file_path="/tmp/doc.txt",
                dataset_id=sample_dataset.id,
                user_id=sample_user["id"],
            )
            session.add(doc)
            await session.commit()

        datasets, total = await dataset_service.list_datasets(
            user_id=sample_user["id"]
        )
        assert total == 1
        assert datasets[0].document_count == 1


# ════════════════════════════════════════════════════════════
# 异常错误码验证
# ════════════════════════════════════════════════════════════


class TestDatasetServiceErrors:
    """数据集服务异常属性验证"""

    def test_dataset_service_error_defaults(self):
        """DatasetServiceError 应具有默认值"""
        err = DatasetServiceError()
        assert err.code == "dataset_service_error"
        assert err.message == "数据集服务错误"

    def test_dataset_not_found_error(self):
        """DatasetNotFound 应包含数据集 ID"""
        err = DatasetNotFound("ds-001")
        assert err.code == "dataset_not_found"
        assert "ds-001" in str(err)

    def test_dataset_permission_denied_error(self):
        """DatasetPermissionDenied 应包含数据集 ID"""
        err = DatasetPermissionDenied("ds-001")
        assert err.code == "dataset_permission_denied"
        assert "ds-001" in str(err)
