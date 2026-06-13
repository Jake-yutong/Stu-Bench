from fastapi import APIRouter, HTTPException, Response

from backend.app.data.schemas import RunConfig
from backend.app.services.data_service import EpisodeNotFoundError, get_episode
from backend.app.services.export_service import load_run, new_run_id, persist_run, run_to_csv
from backend.app.services.judge_service import judge_episode
from backend.app.services.runner import run_episode

router = APIRouter()


@router.post("")
async def create_run(config: RunConfig) -> dict[str, object]:
    results = []
    for episode_id in config.episode_ids:
        try:
            episode = get_episode(episode_id)
        except EpisodeNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"Episode not found: {episode_id}",
            ) from exc
        result = await run_episode(episode, config.mode, config.student_provider)
        judged = await judge_episode(episode, result, config.judge_provider)
        results.append(judged)
    run_id = new_run_id()
    return persist_run(run_id, config, results)


@router.get("/{run_id}")
def read_run(run_id: str) -> dict[str, object]:
    return load_run(run_id)


@router.get("/{run_id}/events")
def read_run_events(run_id: str) -> dict[str, object]:
    payload = load_run(run_id)
    return {
        "run_id": run_id,
        "events": [{"type": "completed", "count": len(payload["results"])}],
    }


@router.get("/{run_id}/export.json")
def export_json(run_id: str) -> dict[str, object]:
    return load_run(run_id)


@router.get("/{run_id}/export.csv")
def export_csv(run_id: str) -> Response:
    csv_text = run_to_csv(load_run(run_id))
    return Response(content=csv_text, media_type="text/csv")
