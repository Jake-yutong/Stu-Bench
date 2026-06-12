from fastapi.testclient import TestClient

from backend.app.main import app


def assert_no_key_named(value, key_name: str) -> None:
    if isinstance(value, dict):
        assert key_name not in value
        for nested_value in value.values():
            assert_no_key_named(nested_value, key_name)
    elif isinstance(value, list):
        for nested_value in value:
            assert_no_key_named(nested_value, key_name)


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


def test_list_episodes_returns_demo_summaries():
    client = TestClient(app)
    response = client.get("/api/episodes")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["episodes"]) >= 1
    first = payload["episodes"][0]
    assert {"episode_id", "question_id", "intervention_id", "problem_preview"} <= set(first)


def test_get_episode_returns_scs_but_not_ecs_by_default():
    client = TestClient(app)
    list_response = client.get("/api/episodes")
    episode_id = list_response.json()["episodes"][0]["episode_id"]

    response = client.get(f"/api/episodes/{episode_id}")
    assert response.status_code == 200
    payload = response.json()
    assert "scs" in payload["lcs"]
    assert "ecs" not in payload["lcs"]
    assert_no_key_named(payload, "ground_truth_answer")


def test_get_episode_returns_404_for_unknown_episode():
    client = TestClient(app)
    response = client.get("/api/episodes/not-real")

    assert response.status_code == 404
    assert response.json() == {"detail": "Episode not found"}
