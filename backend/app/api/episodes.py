from fastapi import APIRouter, HTTPException

from backend.app.services.data_service import (
    EpisodeNotFoundError,
    get_episode,
    list_episode_summaries,
    public_episode_detail,
)

router = APIRouter()


@router.get("")
def list_episodes() -> dict[str, object]:
    return {"episodes": list_episode_summaries()}


@router.get("/{episode_id}")
def read_episode(episode_id: str) -> dict[str, object]:
    try:
        episode = get_episode(episode_id)
    except EpisodeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Episode not found") from exc
    return public_episode_detail(episode)
