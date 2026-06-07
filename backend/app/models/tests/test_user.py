"""用户模型测试"""

import pytest
from sqlalchemy.exc import IntegrityError

from ..user import User


class TestUserModel:
    """测试 User ORM 模型"""

    def test_create_user(self, session):
        """测试创建用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role="user",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None
        assert len(user.id) == 36  # UUID 长度
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.role == "user"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_username_unique(self, session):
        """测试用户名唯一约束"""
        user1 = User(
            username="unique_user",
            email="user1@example.com",
            password_hash="hash1",
        )
        session.add(user1)
        session.commit()

        user2 = User(
            username="unique_user",
            email="user2@example.com",
            password_hash="hash2",
        )
        session.add(user2)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_email_unique(self, session):
        """测试邮箱唯一约束"""
        user1 = User(
            username="user_a",
            email="same@example.com",
            password_hash="hash1",
        )
        session.add(user1)
        session.commit()

        user2 = User(
            username="user_b",
            email="same@example.com",
            password_hash="hash2",
        )
        session.add(user2)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_default_role(self, session):
        """测试默认角色"""
        user = User(
            username="default_user",
            email="default@example.com",
            password_hash="hash",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.role == "user"

    def test_default_is_active(self, session):
        """测试默认活跃状态"""
        user = User(
            username="active_user",
            email="active@example.com",
            password_hash="hash",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.is_active is True

    def test_user_str_repr(self, session):
        """测试 __repr__ 输出"""
        user = User(
            username="repr_user",
            email="repr@example.com",
            password_hash="hash",
        )
        session.add(user)
        session.commit()

        repr_str = repr(user)
        assert "User" in repr_str
        assert "repr_user" in repr_str
