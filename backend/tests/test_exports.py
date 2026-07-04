from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import run_manager


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
    run_manager.reset_run_state()
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
    assert response.json()["status"] in {"queued", "running"}
    assert response.json()["total"] == 1
    events_payload = _wait_for_completion(client, run_id)
    assert events_payload["status"] == "completed"
    assert events_payload["completed"] == 1
    assert events_payload["total"] == 1
    assert events_payload["results"][0]["status"] == "succeeded"
    assert events_payload["results"][0]["judge_scores"]["lrs"] == 0.78
    assert "learning_trajectory_plausibility" not in events_payload["results"][0]["judge_scores"]

    run_payload = client.get(f"/api/runs/{run_id}").json()
    assert run_payload["results"][0]["status"] == "succeeded"
    assert run_payload["results"][0]["judge_scores"]["lrs"] == 0.78

    csv_response = client.get(f"/api/runs/{run_id}/export.csv")
    assert csv_response.status_code == 200
    assert "lrs,isf,ma,su,ktc,occ" in csv_response.text
    assert "learning_trajectory_plausibility" not in csv_response.text
    assert episode_id in csv_response.text

    json_response = client.get(f"/api/runs/{run_id}/export.json")
    assert json_response.status_code == 200
    assert json_response.json()["run_id"] == run_id
    assert json_response.json()["config"]["student_provider"]["api_key"] == "[redacted]"
    assert json_response.json()["config"]["judge_provider"]["api_key"] == "[redacted]"


def test_export_json_redacts_legacy_run_files(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.app.services.export_service.RUN_STORAGE_DIR", tmp_path)
    run_manager.reset_run_state()
    run_id = "run-legacy-secret"
    (tmp_path / f"{run_id}.json").write_text(
        """
{
  "run_id": "run-legacy-secret",
  "created_at": "2026-07-05T00:00:00+00:00",
  "config": {
    "mode": "context_engineered",
    "student_provider": {
      "preset": "qwen",
      "base_url": "https://example.test/v1",
      "api_key": "sk-student-secret",
      "model": "student",
      "temperature": 0.2
    },
    "judge_provider": {
      "preset": "qwen",
      "base_url": "https://example.test/v1",
      "api_key": "sk-judge-secret",
      "model": "judge",
      "temperature": 0.2
    },
    "episode_ids": ["episode-1"]
  },
  "results": []
}
""",
        encoding="utf-8",
    )

    client = TestClient(app)
    response = client.get(f"/api/runs/{run_id}/export.json")

    assert response.status_code == 200
    payload = response.json()
    assert "sk-student-secret" not in response.text
    assert "sk-judge-secret" not in response.text
    assert payload["config"]["student_provider"]["api_key"] == "[redacted]"
    assert payload["config"]["judge_provider"]["api_key"] == "[redacted]"


def test_create_run_returns_404_for_unknown_episode(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.app.services.export_service.RUN_STORAGE_DIR", tmp_path)
    run_manager.reset_run_state()
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


def test_reading_unknown_run_returns_404(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.app.services.export_service.RUN_STORAGE_DIR", tmp_path)
    run_manager.reset_run_state()
    client = TestClient(app)

    response = client.get("/api/runs/not-real")
    events_response = client.get("/api/runs/not-real/events")
    csv_response = client.get("/api/runs/not-real/export.csv")

    assert response.status_code == 404
    assert events_response.status_code == 404
    assert csv_response.status_code == 404


def _wait_for_completion(client: TestClient, run_id: str) -> dict[str, object]:
    for _ in range(20):
        response = client.get(f"/api/runs/{run_id}/events")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
    raise AssertionError(f"Run {run_id} did not finish")
