import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies.providers import get_model_provider
from apps.api.main import app


@pytest.fixture
def client(fake_provider):
    app.dependency_overrides[get_model_provider] = lambda: fake_provider
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_send_message_returns_recommendation_shape(client):
    response = client.post(
        "/v1/sessions/demo/messages",
        json={"message": "I want paneer tonight for two under 700"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "recommendation_id" in body
    assert "intent" in body
    assert "candidates" in body
    assert "recommended_candidate_id" in body
    assert "explanation" in body
    assert "errors" in body
    assert isinstance(body["candidates"], list)


def test_send_message_missing_field_is_422(client):
    response = client.post("/v1/sessions/demo/messages", json={})
    assert response.status_code == 422
