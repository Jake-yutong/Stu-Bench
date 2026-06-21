from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.dataset_service import dataset_artifact_summary, load_annotation_schema, load_test_manifest


def test_loads_official_test_manifest():
    load_test_manifest.cache_clear()
    rows = load_test_manifest()

    assert len(rows) == 395
    assert {row["split"] for row in rows} == {"test"}
    assert rows[0]["episode_id"].startswith("eedi-")


def test_loads_annotation_schema_v0_1():
    load_annotation_schema.cache_clear()
    schema = load_annotation_schema()

    assert schema["title"] == "Stu-Bench Annotation Schema v0.1"
    assert schema["properties"]["annotation_version"]["const"] == "v0.1"
    assert {"human_verified", "adjudicated"} <= set(schema["$defs"]["provenance"]["enum"])


def test_dataset_summary_marks_metric_statuses_by_annotation_readiness():
    summary = dataset_artifact_summary()
    statuses = {item["metric_id"]: item["current_status"] for item in summary["metric_statuses"]}

    assert summary["official_split"] == "anchored-dialogues/test.csv"
    assert summary["episode_count"] == 395
    assert summary["unique_questions"] == 324
    assert statuses["lrs"] == "judge_estimated"
    assert statuses["ktc"] == "judge_estimated"
    assert statuses["formula_kts"] == "pending_annotation"
    assert statuses["formula_uptake"] == "pending_annotation"


def test_dataset_api_returns_manifest_and_schema_summary():
    client = TestClient(app)
    response = client.get("/api/dataset")

    assert response.status_code == 200
    payload = response.json()
    assert payload["episode_count"] == 395
    assert payload["annotation_schema"]["annotation_version"] == "v0.1"
    assert payload["annotation_schema"]["gold_provenance_values"] == ["human_verified", "adjudicated"]
    assert len(payload["metric_statuses"]) >= 6
