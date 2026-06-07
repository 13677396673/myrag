"""数据集模型测试"""

from ..user import User
from ..dataset import Dataset


class TestDatasetModel:
    """测试 Dataset ORM 模型"""

    def _create_user(self, session) -> User:
        user = User(
            username="ds_user",
            email="ds@example.com",
            password_hash="hash",
        )
        session.add(user)
        session.flush()
        return user

    def test_create_dataset(self, session):
        """测试创建数据集"""
        user = self._create_user(session)
        dataset = Dataset(
            name="测试数据集",
            description="这是一个测试数据集",
            user_id=user.id,
        )
        session.add(dataset)
        session.commit()
        session.refresh(dataset)

        assert dataset.id is not None
        assert dataset.name == "测试数据集"
        assert dataset.description == "这是一个测试数据集"
        assert dataset.user_id == user.id
        assert dataset.created_at is not None

    def test_dataset_owner_relationship(self, session):
        """测试用户与数据集的关系（正向）"""
        user = self._create_user(session)
        dataset = Dataset(
            name="关系测试集",
            description="测试关系",
            user_id=user.id,
        )
        session.add(dataset)
        session.commit()
        session.refresh(dataset)

        assert dataset.owner is not None
        assert dataset.owner.id == user.id
        assert dataset.owner.username == "ds_user"

    def test_user_datasets_relationship(self, session):
        """测试用户与数据集的关系（反向）"""
        user = self._create_user(session)
        ds1 = Dataset(name="集1", description="", user_id=user.id)
        ds2 = Dataset(name="集2", description="", user_id=user.id)
        session.add_all([ds1, ds2])
        session.commit()

        # 刷新 user 实例以加载关系
        session.refresh(user)
        # backref datasets 默认是 select 模式，返回列表
        datasets = list(user.datasets)
        assert len(datasets) == 2
        names = {d.name for d in datasets}
        assert names == {"集1", "集2"}

    def test_dataset_default_description(self, session):
        """测试 description 默认可为空"""
        user = self._create_user(session)
        dataset = Dataset(
            name="无描述集",
            user_id=user.id,
        )
        session.add(dataset)
        session.commit()
        session.refresh(dataset)

        assert dataset.description is None

    def test_dataset_repr(self, session):
        """测试 __repr__ 输出"""
        user = self._create_user(session)
        dataset = Dataset(
            name="repr集",
            user_id=user.id,
        )
        session.add(dataset)
        session.commit()

        repr_str = repr(dataset)
        assert "Dataset" in repr_str
        assert "repr集" in repr_str
