import asyncio
from datetime import datetime, timezone
from typing import Literal

from backend.app.data.schemas import EpisodeRecord, EpisodeResult, RunConfig
from backend.app.services.export_service import new_run_id, persist_run
from backend.app.services.judge_service import judge_episode
from backend.app.services.runner import run_episode

RunState = Literal["queued", "running", "completed", "failed"]

_runs: dict[str, dict[str, object]] = {}
EPISODE_CONDITION_TIMEOUT_SECONDS = 180
MAX_CONCURRENT_EPISODE_CONDITIONS = 2


def reset_run_state() -> None:
    _runs.clear()


def start_run(config: RunConfig, episodes: list[EpisodeRecord]) -> dict[str, object]:
    run_id = new_run_id()
    modes = config.selected_modes()
    _runs[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "total": len(episodes) * len(modes),
        "completed": 0,
        "current_episode_id": None,
        "current_mode": None,
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
    results_by_index: dict[int, EpisodeResult] = {}
    modes = config.selected_modes()
    work_items = [
        (index, episode, mode)
        for index, (episode, mode) in enumerate(
            (episode, mode) for episode in episodes for mode in modes
        )
    ]
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_EPISODE_CONDITIONS)
    status["status"] = "running"
    try:
        async def run_work_item(
            index: int,
            episode: EpisodeRecord,
            mode,
        ) -> tuple[int, EpisodeResult]:
            async with semaphore:
                status["current_episode_id"] = episode.episode_id
                status["current_mode"] = mode.value
                result = await _run_episode_condition_with_timeout(episode, mode, config)
                return index, result

        tasks = [
            asyncio.create_task(run_work_item(index, episode, mode))
            for index, episode, mode in work_items
        ]
        for task in asyncio.as_completed(tasks):
            index, result = await task
            results_by_index[index] = result
            completed_results = [
                results_by_index[item_index]
                for item_index in sorted(results_by_index)
            ]
            status["completed"] = len(completed_results)
            status["results"] = [item.model_dump(mode="json") for item in completed_results]
        results = [results_by_index[index] for index in sorted(results_by_index)]
        payload = persist_run(run_id, config, results)
        status["status"] = "completed"
        status["current_episode_id"] = None
        status["current_mode"] = None
        status["results"] = payload["results"]
        status["completed_at"] = payload["created_at"]
    except Exception as exc:  # pragma: no cover - defensive boundary for background task
        status["status"] = "failed"
        status["error_message"] = str(exc)


async def _run_episode_condition_with_timeout(
    episode: EpisodeRecord,
    mode,
    config: RunConfig,
) -> EpisodeResult:
    try:
        return await asyncio.wait_for(
            _run_episode_condition(episode, mode, config),
            timeout=EPISODE_CONDITION_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        return EpisodeResult(
            episode_id=episode.episode_id,
            mode=mode,
            status="failed",
            error_message=(
                f"Episode-condition timed out after "
                f"{EPISODE_CONDITION_TIMEOUT_SECONDS} seconds."
            ),
        )


async def _run_episode_condition(
    episode: EpisodeRecord,
    mode,
    config: RunConfig,
) -> EpisodeResult:
    result = await run_episode(episode, mode, config.student_provider)
    return await judge_episode(episode, result, config.judge_provider)
