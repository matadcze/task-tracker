"""Tests for health check endpoint"""

from fastapi.testclient import TestClient
from src.api.app import create_app


client = TestClient(create_app())


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Project Name API"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"
