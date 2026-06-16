import csv
import json
from datetime import datetime, timezone
from io import StringIO
from uuid import uuid4

from backend.app.core.config import RUN_STORAGE_DIR
from backend.app.data.schemas import EpisodeResult, RunConfig


class RunNotFoundError(FileNotFoundError):
    pass


def new_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"run-{timestamp}-{uuid4().hex[:8]}"


def persist_run(run_id: str, config: RunConfig, results: list[EpisodeResult]) -> dict[str, object]:
    RUN_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config.model_dump(mode="json"),
        "results": [result.model_dump(mode="json") for result in results],
    }
    (RUN_STORAGE_DIR / f"{run_id}.json").write_text(json.dumps(payload, indent=2))
    return payload


def load_run(run_id: str) -> dict[str, object]:
    path = RUN_STORAGE_DIR / f"{run_id}.json"
    if not path.exists():
        raise RunNotFoundError(run_id)
    return json.loads(path.read_text())


def run_to_csv(payload: dict[str, object]) -> str:
    output = StringIO()
    fieldnames = [
        "run_id",
        "episode_id",
        "mode",
        "status",
        "lrs",
        "isf",
        "ma",
        "su",
        "ktc",
        "occ",
        "formula_kts",
        "formula_uptake",
        "formula_over_improve",
        "metric_status",
        "error_message",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for result in payload["results"]:
        scores = result.get("judge_scores") or {}
        formula = scores.get("formula_metrics") or {}
        writer.writerow(
            {
                "run_id": payload["run_id"],
                "episode_id": result["episode_id"],
                "mode": result["mode"],
                "status": result["status"],
                "lrs": scores.get("lrs"),
                "isf": scores.get("isf"),
                "ma": scores.get("ma"),
                "su": scores.get("su"),
                "ktc": scores.get("ktc"),
                "occ": scores.get("occ"),
                "formula_kts": formula.get("kts"),
                "formula_uptake": formula.get("uptake"),
                "formula_over_improve": formula.get("over_improve"),
                "metric_status": formula.get("status"),
                "error_message": result.get("error_message"),
            }
        )
    return output.getvalue()
