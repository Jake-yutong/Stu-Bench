import csv
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.app.core.config import ANNOTATION_SCHEMA_PATH, EEDI_TEST_MANIFEST_PATH
from backend.app.data.schemas import MetricStatus


@lru_cache(maxsize=1)
def load_test_manifest(path: Path = EEDI_TEST_MANIFEST_PATH) -> tuple[dict[str, str], ...]:
    with path.open(newline="") as file:
        return tuple(csv.DictReader(file))


@lru_cache(maxsize=1)
def load_annotation_schema(path: Path = ANNOTATION_SCHEMA_PATH) -> dict[str, Any]:
    return json.loads(path.read_text())


def _count_unique(rows: tuple[dict[str, str], ...], key: str) -> int:
    return len({row[key] for row in rows if row.get(key)})


def _counter(rows: tuple[dict[str, str], ...], key: str) -> dict[str, int]:
    counts = Counter(row.get(key) or "unknown" for row in rows)
    return dict(sorted(counts.items()))


def metric_status_catalog() -> list[dict[str, str]]:
    return [
        {
            "metric_id": "lrs",
            "display_name": "Learner Realism Score",
            "current_status": MetricStatus.judge_estimated.value,
            "computed_when": "Validated evaluator or adjudicated human rubric exists.",
        },
        {
            "metric_id": "isf",
            "display_name": "Initial State Fidelity",
            "current_status": MetricStatus.judge_estimated.value,
            "computed_when": "Human-verified initial learner KC state is available.",
        },
        {
            "metric_id": "ma",
            "display_name": "Mistake Authenticity",
            "current_status": MetricStatus.judge_estimated.value,
            "computed_when": "Human-verified misconception path and generated-turn labels are available.",
        },
        {
            "metric_id": "su",
            "display_name": "Scaffolding Uptake",
            "current_status": MetricStatus.judge_estimated.value,
            "computed_when": "Human-verified scaffold labels and uptake evidence are available.",
        },
        {
            "metric_id": "ktc",
            "display_name": "KC Transition Consistency",
            "current_status": MetricStatus.judge_estimated.value,
            "computed_when": "Human-verified or adjudicated KC state-by-turn labels are available.",
        },
        {
            "metric_id": "occ",
            "display_name": "Over-Competence Control",
            "current_status": MetricStatus.judge_estimated.value,
            "computed_when": "Human-verified over-improvement labels are available.",
        },
        {
            "metric_id": "formula_kts",
            "display_name": "Formula KTS",
            "current_status": MetricStatus.pending_annotation.value,
            "computed_when": "Reference and generated KC transitions are structured annotations.",
        },
        {
            "metric_id": "formula_uptake",
            "display_name": "Formula Uptake",
            "current_status": MetricStatus.pending_annotation.value,
            "computed_when": "Generated turns have structured uptake labels.",
        },
        {
            "metric_id": "formula_over_improve",
            "display_name": "Formula OverImprove",
            "current_status": MetricStatus.pending_annotation.value,
            "computed_when": "Generated turns have structured over-improvement labels.",
        },
    ]


def dataset_artifact_summary() -> dict[str, object]:
    rows = load_test_manifest()
    schema = load_annotation_schema()
    provenance_enum = schema["$defs"]["provenance"]["enum"]

    return {
        "official_split": "anchored-dialogues/test.csv",
        "episode_count": len(rows),
        "unique_questions": _count_unique(rows, "question_id"),
        "subject_distribution": _counter(rows, "subject"),
        "length_distribution": _counter(rows, "length_bucket"),
        "manifest": {
            "path": str(EEDI_TEST_MANIFEST_PATH),
            "row_count": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
        },
        "annotation_schema": {
            "path": str(ANNOTATION_SCHEMA_PATH),
            "title": schema.get("title"),
            "annotation_version": schema["properties"]["annotation_version"]["const"],
            "required_fields": schema.get("required", []),
            "provenance_values": provenance_enum,
            "gold_provenance_values": ["human_verified", "adjudicated"],
        },
        "metric_statuses": metric_status_catalog(),
    }
