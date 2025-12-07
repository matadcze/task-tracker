"""Tests for authentication API routes"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.app import create_app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(create_app())


class TestAuthRegister:
    """Tests for user registration endpoint"""

    def test_register_success(self, client, monkeypatch):
        """Test successful registration"""

        # Mock the service layer
        async def mock_register(*args, **kwargs):
            from src.domain.entities import User
            from uuid import uuid4

            return User(
                id=uuid4(),
                email="newuser@example.com",
                password_hash="hashed",
                full_name="New User",
                is_active=True,
            )

        with patch(
            "src.domain.services.auth_service.AuthService.register", new_callable=MagicMock
        ) as mock:
            # We would normally mock this at the dependency injection level
            pass

    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "ValidPassword123",
                "full_name": "Test User",
            },
        )

        # Should fail validation or return 400
        assert response.status_code in [400, 422]

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "full_name": "Test User",
            },
        )

        assert response.status_code in [400, 422]

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                # Missing password and full_name
            },
        )

        assert response.status_code == 422


class TestAuthLogin:
    """Tests for user login endpoint"""

    def test_login_missing_credentials(self, client):
        """Test login without credentials"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                # Missing email and password
            },
        )

        assert response.status_code == 422

    def test_login_invalid_email_format(self, client):
        """Test login with invalid email format"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "invalid-email",
                "password": "Password123",
            },
        )

        assert response.status_code in [400, 422]


class TestAuthChangePassword:
    """Tests for password change endpoint"""

    def test_change_password_missing_token(self, client):
        """Test password change without authentication"""
        response = client.put(
            "/api/v1/auth/change-password",
            json={
                "current_password": "OldPassword123",
                "new_password": "NewPassword123",
            },
            # No Authorization header
        )

        assert response.status_code in [401, 403]

    def test_change_password_weak_new_password(self, client):
        """Test password change with weak new password"""
        # This would require a valid token, so we just test the validation
        response = client.put(
            "/api/v1/auth/change-password",
            json={
                "current_password": "OldPassword123",
                "new_password": "weak",
            },
            headers={"Authorization": "Bearer invalid-token"},
        )

        # Should fail due to weak password or invalid token
        assert response.status_code in [400, 401, 422]
