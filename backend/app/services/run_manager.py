import asyncio
from datetime import datetime, timezone
from typing import Literal

from backend.app.data.schemas import EpisodeRecord, EpisodeResult, RunConfig
from backend.app.services.export_service import new_run_id, persist_run
from backend.app.services.judge_service import judge_episode
from backend.app.services.runner import run_episode

RunState = Literal["queued", "running", "completed", "failed"]

_runs: dict[str, dict[str, object]] = {}


def reset_run_state() -> None:
    _runs.clear()


def start_run(config: RunConfig, episodes: list[EpisodeRecord]) -> dict[str, object]:
    run_id = new_run_id()
    _runs[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "total": len(episodes),
        "completed": 0,
        "current_episode_id": None,
        "results": [],
        "error_message": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    asyncio.create_task(_execute_run(run_id, config, episodes))
    return get_run_status(run_id)


def run_exists(run_id: str) -> bool:
    return run_id in _runs


def get_run_status(run_id: str) -> dict[str, object]:
    if run_id not in _runs:
        raise KeyError(run_id)
    return dict(_runs[run_id])


async def _execute_run(run_id: str, config: RunConfig, episodes: list[EpisodeRecord]) -> None:
    status = _runs[run_id]
    results: list[EpisodeResult] = []
    status["status"] = "running"
    try:
        for episode in episodes:
            status["current_episode_id"] = episode.episode_id
            result = await run_episode(episode, config.mode, config.student_provider)
            judged = await judge_episode(episode, result, config.judge_provider)
            results.append(judged)
            status["completed"] = len(results)
            status["results"] = [item.model_dump(mode="json") for item in results]
        payload = persist_run(run_id, config, results)
        status["status"] = "completed"
        status["current_episode_id"] = None
        status["results"] = payload["results"]
        status["completed_at"] = payload["created_at"]
    except Exception as exc:  # pragma: no cover - defensive boundary for background task
        status["status"] = "failed"
        status["error_message"] = str(exc)
