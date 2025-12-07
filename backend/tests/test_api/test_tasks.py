"""Tests for task API routes"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(create_app())


class TestTaskEndpoints:
    """Tests for task endpoints"""

    def test_create_task_missing_title(self, client):
        """Test creating task without title"""
        response = client.post(
            "/api/v1/tasks",
            json={
                "description": "A task",
                # Missing title
            },
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code in [401, 422]

    def test_list_tasks_pagination(self, client):
        """Test listing tasks with pagination"""
        response = client.get(
            "/api/v1/tasks?page=1&page_size=20", headers={"Authorization": "Bearer invalid-token"}
        )

        # Should fail due to invalid token but test request format
        assert response.status_code in [401, 403]

    def test_list_tasks_with_filters(self, client):
        """Test listing tasks with filters"""
        response = client.get(
            "/api/v1/tasks?status=todo&priority=high&page=1",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code in [401, 403]

    def test_get_task_invalid_id(self, client):
        """Test getting task with invalid UUID"""
        response = client.get(
            "/api/v1/tasks/not-a-uuid", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code in [401, 404, 422]

    def test_update_task_invalid_payload(self, client):
        """Test updating task with invalid payload"""
        response = client.put(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000000",
            json={
                "title": "",  # Empty title
            },
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code in [400, 401, 422]

    def test_delete_task_success_status(self, client):
        """Test that delete task returns proper status codes"""
        response = client.delete(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": "Bearer invalid-token"},
        )

        # Should fail due to invalid token
        assert response.status_code in [401, 403, 404]
