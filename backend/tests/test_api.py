from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint_returns_ok():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "stu-bench-demo"}


def test_health_endpoint_allows_localhost_3000_origin():
    client = TestClient(app)
    origin = "http://localhost:3000"

    response = client.get("/api/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_health_endpoint_allows_loopback_3000_origin():
    client = TestClient(app)
    origin = "http://127.0.0.1:3000"

    response = client.get("/api/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
