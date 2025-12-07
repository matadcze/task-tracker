"""Tests for JWTProvider"""

import pytest
from datetime import datetime, timedelta, timezone
from src.core.time import utc_now
from jose import jwt

from src.infrastructure.auth.jwt_provider import JWTProvider
from src.domain.exceptions import AuthenticationError
from src.core.config import settings


class TestJWTProviderAccessToken:
    """Tests for JWTProvider access token creation and verification"""

    def test_create_access_token(self, sample_user_id):
        """Test creating an access token"""
        token = JWTProvider.create_access_token(sample_user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token structure
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(sample_user_id)
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_access_token_custom_expiration(self, sample_user_id):
        """Test creating an access token with custom expiration"""
        custom_delta = timedelta(hours=1)
        token = JWTProvider.create_access_token(sample_user_id, expires_delta=custom_delta)

        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Check that expiration is approximately 1 hour from now
        diff = (exp_time - now).total_seconds()
        assert 3590 < diff < 3610  # Allow 10 second variance

    def test_create_refresh_token(self, sample_user_id):
        """Test creating a refresh token"""
        token = JWTProvider.create_refresh_token(sample_user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token structure
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(sample_user_id)
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_create_refresh_token_custom_expiration(self, sample_user_id):
        """Test creating a refresh token with custom expiration"""
        custom_delta = timedelta(days=14)
        token = JWTProvider.create_refresh_token(sample_user_id, expires_delta=custom_delta)

        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Check that expiration is approximately 14 days from now
        diff = (exp_time - now).total_seconds()
        assert 1209590 < diff < 1209610  # Allow 10 second variance


class TestJWTProviderVerification:
    """Tests for JWTProvider token verification"""

    def test_verify_access_token(self, valid_access_token, sample_user_id):
        """Test verifying a valid access token"""
        payload = JWTProvider.verify_token(valid_access_token, token_type="access")

        assert payload["sub"] == str(sample_user_id)
        assert payload["type"] == "access"

    def test_verify_refresh_token(self, valid_refresh_token, sample_user_id):
        """Test verifying a valid refresh token"""
        payload = JWTProvider.verify_token(valid_refresh_token, token_type="refresh")

        assert payload["sub"] == str(sample_user_id)
        assert payload["type"] == "refresh"

    def test_verify_expired_token(self, expired_access_token):
        """Test verifying an expired token"""
        with pytest.raises(AuthenticationError, match="Token has expired"):
            JWTProvider.verify_token(expired_access_token, token_type="access")

    def test_verify_wrong_token_type(self, valid_refresh_token):
        """Test verifying a token with wrong type"""
        with pytest.raises(AuthenticationError, match="Invalid token type"):
            JWTProvider.verify_token(valid_refresh_token, token_type="access")

    def test_verify_malformed_token(self):
        """Test verifying a malformed token"""
        with pytest.raises(AuthenticationError, match="Could not validate credentials"):
            JWTProvider.verify_token("not-a-valid-token", token_type="access")

    def test_verify_token_with_invalid_signature(self, sample_user_id):
        """Test verifying a token with invalid signature"""
        # Create a token with wrong secret
        token = jwt.encode(
            {
                "sub": str(sample_user_id),
                "exp": utc_now() + timedelta(minutes=15),
                "type": "access",
            },
            "wrong-secret-key",
            algorithm="HS256",
        )

        with pytest.raises(AuthenticationError, match="Could not validate credentials"):
            JWTProvider.verify_token(token, token_type="access")

    def test_verify_token_missing_required_claims(self):
        """Test verifying a token missing required claims"""
        # Create a token without required claims
        token = jwt.encode(
            {
                "sub": "user-123",
                # Missing 'exp' and 'type'
            },
            settings.jwt_secret_key,
            algorithm="HS256",
        )

        with pytest.raises(AuthenticationError, match="Token missing required claims"):
            JWTProvider.verify_token(token, token_type="access")


class TestJWTProviderGetUserID:
    """Tests for JWTProvider.get_user_id_from_token()"""

    def test_get_user_id_from_token(self, valid_access_token, sample_user_id):
        """Test extracting user ID from token"""
        user_id = JWTProvider.get_user_id_from_token(valid_access_token)

        assert user_id == sample_user_id

    def test_get_user_id_from_expired_token(self, expired_access_token):
        """Test extracting user ID from expired token"""
        with pytest.raises(AuthenticationError, match="Token has expired"):
            JWTProvider.get_user_id_from_token(expired_access_token)

    def test_get_user_id_invalid_token(self):
        """Test extracting user ID from invalid token"""
        with pytest.raises(AuthenticationError):
            JWTProvider.get_user_id_from_token("invalid-token")

    def test_get_user_id_invalid_uuid(self):
        """Test extracting user ID when sub claim is not a valid UUID"""
        token = jwt.encode(
            {
                "sub": "not-a-uuid",
                "exp": utc_now() + timedelta(minutes=15),
                "type": "access",
            },
            settings.jwt_secret_key,
            algorithm="HS256",
        )

        with pytest.raises(AuthenticationError, match="Invalid user ID in token"):
            JWTProvider.get_user_id_from_token(token)
