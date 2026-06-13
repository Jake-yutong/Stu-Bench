from fastapi import APIRouter, HTTPException, Response

from backend.app.data.schemas import RunConfig
from backend.app.services.data_service import EpisodeNotFoundError, get_episode
from backend.app.services.export_service import RunNotFoundError, load_run, run_to_csv
from backend.app.services.run_manager import get_run_status, run_exists, start_run

router = APIRouter()


@router.post("")
async def create_run(config: RunConfig) -> dict[str, object]:
    episodes = []
    for episode_id in config.episode_ids:
        try:
            episodes.append(get_episode(episode_id))
        except EpisodeNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"Episode not found: {episode_id}",
            ) from exc
    return start_run(config, episodes)


@router.get("/{run_id}")
def read_run(run_id: str) -> dict[str, object]:
    try:
        return load_run(run_id)
    except RunNotFoundError as exc:
        if run_exists(run_id):
            raise HTTPException(status_code=202, detail="Run is still in progress") from exc
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.get("/{run_id}/events")
def read_run_events(run_id: str) -> dict[str, object]:
    try:
        return get_run_status(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.get("/{run_id}/export.json")
def export_json(run_id: str) -> dict[str, object]:
    try:
        return load_run(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.get("/{run_id}/export.csv")
def export_csv(run_id: str) -> Response:
    try:
        csv_text = run_to_csv(load_run(run_id))
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    return Response(content=csv_text, media_type="text/csv")
