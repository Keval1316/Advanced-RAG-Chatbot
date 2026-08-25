import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "health" in data


def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert "services" in data["data"]
    assert "X-Process-Time-Seconds" in response.headers


def test_not_found_endpoint():
    response = client.get("/api/v1/non-existent-route")
    assert response.status_code == 404
