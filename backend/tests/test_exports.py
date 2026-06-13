from fastapi.testclient import TestClient

from backend.app.main import app


def _mock_provider(model: str) -> dict[str, object]:
    return {
        "preset": "mock",
        "base_url": "mock://local",
        "api_key": "mock",
        "model": model,
        "temperature": 0.2,
    }


def test_create_run_and_export_json_and_csv(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.app.services.export_service.RUN_STORAGE_DIR", tmp_path)
    client = TestClient(app)
    episode_id = client.get("/api/episodes").json()["episodes"][0]["episode_id"]

    response = client.post(
        "/api/runs",
        json={
            "mode": "context_engineered",
            "student_provider": _mock_provider("mock-student"),
            "judge_provider": _mock_provider("mock-judge"),
            "episode_ids": [episode_id],
        },
    )

    assert response.status_code == 200
    run_id = response.json()["run_id"]
    run_payload = client.get(f"/api/runs/{run_id}").json()
    assert run_payload["results"][0]["status"] == "succeeded"
    assert run_payload["results"][0]["judge_scores"]["overall_realism"] == 78
    events_response = client.get(f"/api/runs/{run_id}/events")
    assert events_response.status_code == 200
    assert events_response.json()["events"] == [{"type": "completed", "count": 1}]

    csv_response = client.get(f"/api/runs/{run_id}/export.csv")
    assert csv_response.status_code == 200
    assert "overall_realism" in csv_response.text
    assert episode_id in csv_response.text

    json_response = client.get(f"/api/runs/{run_id}/export.json")
    assert json_response.status_code == 200
    assert json_response.json()["run_id"] == run_id


def test_create_run_returns_404_for_unknown_episode(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.app.services.export_service.RUN_STORAGE_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={
            "mode": "context_engineered",
            "student_provider": _mock_provider("mock-student"),
            "judge_provider": _mock_provider("mock-judge"),
            "episode_ids": ["not-real"],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Episode not found: not-real"
