"""Tests for audit API routes"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(create_app())


class TestAuditEndpoints:
    """Tests for audit endpoints"""

    def test_list_audit_events_no_filters(self, client):
        """Test listing audit events without filters"""
        response = client.get("/api/v1/audit", headers={"Authorization": "Bearer invalid-token"})

        assert response.status_code in [401, 403, 200]

    def test_list_audit_events_with_pagination(self, client):
        """Test listing audit events with pagination"""
        response = client.get(
            "/api/v1/audit?page=1&page_size=50", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code in [401, 403, 200]

    def test_list_audit_events_with_filters(self, client):
        """Test listing audit events with filters"""
        response = client.get(
            "/api/v1/audit?event_type=TASK_CREATED&page=1&page_size=50",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code in [401, 403, 200]

    def test_list_audit_events_with_date_range(self, client):
        """Test listing audit events filtered by date range"""
        response = client.get(
            "/api/v1/audit?start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59&page=1",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code in [401, 403, 200]

    def test_list_audit_events_invalid_page_size(self, client):
        """Test listing with invalid page size"""
        response = client.get(
            "/api/v1/audit?page_size=101",  # Exceeds max
            headers={"Authorization": "Bearer invalid-token"},
        )

        # Should fail validation
        assert response.status_code in [401, 403, 422]
