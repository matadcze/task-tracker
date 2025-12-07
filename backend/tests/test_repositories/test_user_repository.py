"""Tests for UserRepository"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import User
from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.infrastructure.auth.password import PasswordUtils


@pytest.mark.asyncio
class TestUserRepositoryCreate:
    """Tests for UserRepository.create()"""

    async def test_create_user(self, db_session: AsyncSession, sample_user):
        """Test creating a new user"""
        repo = UserRepositoryImpl(db_session)

        result = await repo.create(sample_user)

        assert result.id == sample_user.id
        assert result.email == sample_user.email
        assert result.full_name == sample_user.full_name
        assert result.is_active is True

    async def test_create_user_password_hashed(self, db_session: AsyncSession):
        """Test that password is properly hashed"""
        repo = UserRepositoryImpl(db_session)

        user = User(
            email="test@example.com",
            password_hash=PasswordUtils.hash_password("TestPassword123"),
            full_name="Test User",
            is_active=True,
        )

        result = await repo.create(user)

        assert result.password_hash != "TestPassword123"
        assert result.password_hash.startswith("$2b$")


@pytest.mark.asyncio
class TestUserRepositoryGet:
    """Tests for UserRepository.get_by_id() and get_by_email()"""

    async def test_get_user_by_id(self, db_session: AsyncSession, sample_user):
        """Test retrieving user by ID"""
        repo = UserRepositoryImpl(db_session)

        # Create user first
        created = await repo.create(sample_user)

        # Retrieve it
        result = await repo.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.email == created.email

    async def test_get_user_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent user by ID"""
        from uuid import uuid4

        repo = UserRepositoryImpl(db_session)

        result = await repo.get_by_id(uuid4())

        assert result is None

    async def test_get_user_by_email(self, db_session: AsyncSession, sample_user):
        """Test retrieving user by email"""
        repo = UserRepositoryImpl(db_session)

        # Create user
        created = await repo.create(sample_user)

        # Retrieve by email
        result = await repo.get_by_email(created.email)

        assert result is not None
        assert result.email == created.email

    async def test_get_user_by_email_not_found(self, db_session: AsyncSession):
        """Test getting non-existent user by email"""
        repo = UserRepositoryImpl(db_session)

        result = await repo.get_by_email("nonexistent@example.com")

        assert result is None


@pytest.mark.asyncio
class TestUserRepositoryUpdate:
    """Tests for UserRepository.update()"""

    async def test_update_user_full_name(self, db_session: AsyncSession, sample_user):
        """Test updating user full name"""
        repo = UserRepositoryImpl(db_session)

        # Create user
        created = await repo.create(sample_user)

        # Update
        created.full_name = "Updated Name"
        result = await repo.update(created)

        assert result.full_name == "Updated Name"

    async def test_update_user_is_active(self, db_session: AsyncSession, sample_user):
        """Test updating user active status"""
        repo = UserRepositoryImpl(db_session)

        # Create user
        created = await repo.create(sample_user)

        # Update
        created.is_active = False
        result = await repo.update(created)

        assert result.is_active is False
