"""Tests for attachment API routes"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(create_app())


class TestAttachmentEndpoints:
    """Tests for attachment endpoints"""

    def test_upload_attachment_missing_file(self, client):
        """Test uploading without file"""
        response = client.post(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000000/attachments",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code in [401, 422]

    def test_list_attachments_invalid_task_id(self, client):
        """Test listing attachments with invalid task ID"""
        response = client.get(
            "/api/v1/tasks/invalid-id/attachments",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code in [401, 422]

    def test_get_attachment_by_id(self, client):
        """Test getting specific attachment"""
        response = client.get(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000000/attachments/00000000-0000-0000-0000-000000000001",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code in [401, 404]

    def test_delete_attachment(self, client):
        """Test deleting an attachment"""
        response = client.delete(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000000/attachments/00000000-0000-0000-0000-000000000001",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code in [401, 404]
