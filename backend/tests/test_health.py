from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok_status():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "EstateAI API"
    assert body["version"] == "0.1.0"
