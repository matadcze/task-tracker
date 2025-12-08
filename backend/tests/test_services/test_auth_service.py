"""Tests for AuthService"""

import pytest
from datetime import timedelta
from src.core.time import utc_now
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.domain.services.auth_service import AuthService, AuthTokens
from src.domain.entities import User, RefreshToken
from src.domain.exceptions import ValidationError, AuthenticationError
from src.infrastructure.auth.password import PasswordUtils
from src.infrastructure.auth.jwt_provider import JWTProvider


@pytest.mark.asyncio
class TestAuthServiceRegister:
    """Tests for AuthService.register()"""

    async def test_register_success(
        self, mock_user_repository, mock_refresh_token_repository, mock_metrics_provider
    ):
        """Test successful user registration"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        # Setup mock
        user_id = uuid4()
        created_user = User(
            id=user_id,
            email="newuser@example.com",
            password_hash=PasswordUtils.hash_password("ValidPassword123"),
            full_name="New User",
            is_active=True,
        )
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.create.return_value = created_user

        # Execute
        result = await service.register(
            email="newuser@example.com", password="ValidPassword123", full_name="New User"
        )

        # Assert
        assert result.id == user_id
        assert result.email == "newuser@example.com"
        assert result.full_name == "New User"
        mock_user_repository.get_by_email.assert_called_once_with("newuser@example.com")
        mock_user_repository.create.assert_called_once()
        mock_metrics_provider.track_auth_operation.assert_called_once()
        call_args = mock_metrics_provider.track_auth_operation.call_args
        assert call_args[0] == ("register", "success")

    async def test_register_duplicate_email(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        sample_user,
    ):
        """Test registration with duplicate email"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        mock_user_repository.get_by_email.return_value = sample_user

        with pytest.raises(ValidationError, match="Email already registered"):
            await service.register(
                email="test@example.com", password="ValidPassword123", full_name="Test User"
            )

    async def test_register_invalid_email(
        self, mock_user_repository, mock_refresh_token_repository, mock_metrics_provider
    ):
        """Test registration with invalid email"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        mock_user_repository.get_by_email.return_value = None

        with pytest.raises(ValidationError, match="Invalid email format"):
            await service.register(
                email="invalid-email", password="ValidPassword123", full_name="Test User"
            )

    async def test_register_short_password(
        self, mock_user_repository, mock_refresh_token_repository, mock_metrics_provider
    ):
        """Test registration with password less than 8 characters"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        mock_user_repository.get_by_email.return_value = None

        with pytest.raises(ValidationError, match="Password must be at least 8 characters"):
            await service.register(
                email="test@example.com", password="short", full_name="Test User"
            )

    async def test_register_empty_full_name(
        self, mock_user_repository, mock_refresh_token_repository, mock_metrics_provider
    ):
        """Test registration with empty full name"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        mock_user_repository.get_by_email.return_value = None

        with pytest.raises(ValidationError, match="Full name cannot be empty"):
            await service.register(
                email="test@example.com", password="ValidPassword123", full_name="  "
            )

    async def test_register_strips_whitespace_from_full_name(
        self, mock_user_repository, mock_refresh_token_repository, mock_metrics_provider
    ):
        """Test that full name is stripped of whitespace"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        user_id = uuid4()
        created_user = User(
            id=user_id,
            email="test@example.com",
            password_hash=PasswordUtils.hash_password("ValidPassword123"),
            full_name="Test User",
            is_active=True,
        )
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.create.return_value = created_user

        await service.register(
            email="test@example.com", password="ValidPassword123", full_name="  Test User  "
        )

        # Verify that create was called with stripped name
        create_call_args = mock_user_repository.create.call_args
        created_user_arg = create_call_args[0][0]
        assert created_user_arg.full_name == "Test User"


@pytest.mark.asyncio
class TestAuthServiceLogin:
    """Tests for AuthService.login()"""

    async def test_login_success(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        sample_user,
        mock_rate_limiter,
    ):
        """Test successful login"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(
                access_token_expire_minutes=15,
                refresh_token_expire_days=7,
                jwt_secret_key="test-secret-key",
                jwt_algorithm="HS256",
            ),
            rate_limiter=mock_rate_limiter,
        )

        created_token = RefreshToken(
            id=uuid4(),
            user_id=sample_user.id,
            token_hash="hash123",
            expires_at=utc_now() + timedelta(days=7),
        )

        mock_user_repository.get_by_email.return_value = sample_user
        mock_refresh_token_repository.create.return_value = created_token

        result = await service.login(
            email="test@example.com", password="TestPassword123", client_ip="127.0.0.1"
        )

        assert isinstance(result, AuthTokens)
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "Bearer"
        assert result.expires_in == 15 * 60
        mock_user_repository.get_by_email.assert_called_once_with("test@example.com")

    async def test_login_invalid_email(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        mock_rate_limiter,
    ):
        """Test login with non-existent email"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
            rate_limiter=mock_rate_limiter,
        )

        mock_user_repository.get_by_email.return_value = None

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await service.login(email="nonexistent@example.com", password="AnyPassword123")

    async def test_login_wrong_password(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        sample_user,
        mock_rate_limiter,
    ):
        """Test login with wrong password"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
            rate_limiter=mock_rate_limiter,
        )

        mock_user_repository.get_by_email.return_value = sample_user
        mock_rate_limiter.record_failed_login = AsyncMock()

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await service.login(email="test@example.com", password="WrongPassword123")

        mock_rate_limiter.record_failed_login.assert_called_once()

    async def test_login_inactive_user(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        mock_rate_limiter,
    ):
        """Test login with inactive user"""
        inactive_user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash=PasswordUtils.hash_password("TestPassword123"),
            full_name="Test User",
            is_active=False,
        )

        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
            rate_limiter=mock_rate_limiter,
        )

        mock_user_repository.get_by_email.return_value = inactive_user

        with pytest.raises(AuthenticationError, match="Account is not active"):
            await service.login(email="test@example.com", password="TestPassword123")

    async def test_login_account_locked(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        sample_user,
        mock_rate_limiter,
    ):
        """Test login when account is locked"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
            rate_limiter=mock_rate_limiter,
        )

        mock_user_repository.get_by_email.return_value = sample_user
        mock_rate_limiter.is_account_locked.return_value = (True, 300)  # 5 minutes

        with pytest.raises(AuthenticationError, match="Account locked"):
            await service.login(email="test@example.com", password="TestPassword123")


@pytest.mark.asyncio
class TestAuthServiceRefreshToken:
    """Tests for AuthService.refresh_access_token()"""

    async def test_refresh_token_success(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        sample_user,
        valid_refresh_token,
    ):
        """Test successful token refresh"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(
                access_token_expire_minutes=15,
                refresh_token_expire_days=7,
                jwt_secret_key="test-secret-key",
                jwt_algorithm="HS256",
            ),
        )

        mock_user_repository.get_by_id.return_value = sample_user

        result = await service.refresh_access_token(valid_refresh_token)

        assert result.access_token
        assert result.token_type == "Bearer"
        assert result.expires_in == 15 * 60

    async def test_refresh_token_expired(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        expired_access_token,
    ):
        """Test refresh with expired token"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        with pytest.raises(AuthenticationError):
            await service.refresh_access_token(expired_access_token)

    async def test_refresh_token_invalid(
        self, mock_user_repository, mock_refresh_token_repository, mock_metrics_provider
    ):
        """Test refresh with invalid token"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        with pytest.raises(AuthenticationError):
            await service.refresh_access_token("invalid-token")


@pytest.mark.asyncio
class TestAuthServiceChangePassword:
    """Tests for AuthService.change_password()"""

    async def test_change_password_success(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        sample_user,
    ):
        """Test successful password change"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        updated_user = User(
            id=sample_user.id,
            email=sample_user.email,
            password_hash=PasswordUtils.hash_password("NewPassword123"),
            full_name=sample_user.full_name,
            is_active=True,
        )

        mock_user_repository.get_by_id.return_value = sample_user
        mock_user_repository.update.return_value = updated_user

        result = await service.change_password(
            user_id=sample_user.id,
            current_password="TestPassword123",
            new_password="NewPassword123",
        )

        assert result.id == sample_user.id
        mock_user_repository.get_by_id.assert_called_once_with(sample_user.id)
        mock_user_repository.update.assert_called_once()

    async def test_change_password_wrong_current_password(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        sample_user,
    ):
        """Test password change with wrong current password"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        mock_user_repository.get_by_id.return_value = sample_user

        with pytest.raises(AuthenticationError, match="Current password is incorrect"):
            await service.change_password(
                user_id=sample_user.id,
                current_password="WrongPassword123",
                new_password="NewPassword123",
            )

    async def test_change_password_short_new_password(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        sample_user,
    ):
        """Test password change with new password less than 8 characters"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        mock_user_repository.get_by_id.return_value = sample_user

        with pytest.raises(ValidationError, match="Password must be at least 8 characters"):
            await service.change_password(
                user_id=sample_user.id, current_password="TestPassword123", new_password="short"
            )

    async def test_change_password_revokes_all_tokens(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        sample_user,
    ):
        """Test that password change revokes all refresh tokens"""
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        updated_user = User(
            id=sample_user.id,
            email=sample_user.email,
            password_hash=PasswordUtils.hash_password("NewPassword123"),
            full_name=sample_user.full_name,
            is_active=True,
        )

        mock_user_repository.get_by_id.return_value = sample_user
        mock_user_repository.update.return_value = updated_user
        mock_refresh_token_repository.revoke_by_user_id = AsyncMock()

        await service.change_password(
            user_id=sample_user.id,
            current_password="TestPassword123",
            new_password="NewPassword123",
        )

        mock_refresh_token_repository.revoke_by_user_id.assert_called_once_with(sample_user.id)


@pytest.mark.asyncio
class TestAuthServiceDeleteAccount:
    """Tests for AuthService.delete_account()"""

    async def test_delete_account_success(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_metrics_provider,
        sample_user,
    ):
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        mock_user_repository.get_by_id.return_value = sample_user

        await service.delete_account(user_id=sample_user.id)

        mock_refresh_token_repository.revoke_by_user_id.assert_awaited_once_with(sample_user.id)
        mock_user_repository.delete.assert_awaited_once_with(sample_user.id)
        args, kwargs = mock_metrics_provider.track_auth_operation.call_args
        assert args[0] == "delete_account"
        assert args[1] == "success"

    async def test_delete_account_user_not_found(
        self, mock_user_repository, mock_refresh_token_repository, mock_metrics_provider
    ):
        service = AuthService(
            user_repo=mock_user_repository,
            refresh_token_repo=mock_refresh_token_repository,
            metrics=mock_metrics_provider,
            jwt_provider=JWTProvider,
            password_utils=PasswordUtils,
            settings=MagicMock(),
        )

        mock_user_repository.get_by_id.return_value = None

        with pytest.raises(ValidationError, match="User not found"):
            await service.delete_account(user_id=uuid4())
