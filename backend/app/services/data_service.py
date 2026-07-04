import json
from functools import lru_cache
from pathlib import Path

from backend.app.core.config import DEMO_EPISODES_PATH
from backend.app.data.schemas import EpisodeRecord


class EpisodeNotFoundError(KeyError):
    pass


@lru_cache(maxsize=1)
def load_demo_episodes(path: Path = DEMO_EPISODES_PATH) -> tuple[EpisodeRecord, ...]:
    payload = json.loads(path.read_text())
    return tuple(EpisodeRecord.model_validate(item) for item in payload)


def list_episode_summaries() -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for episode in load_demo_episodes():
        summaries.append(
            {
                "episode_id": episode.episode_id,
                "question_id": episode.question_id,
                "intervention_id": episode.intervention_id,
                "source_split": episode.source_split,
                "subject": episode.subject,
                "topic": episode.topic,
                "problem_preview": episode.problem.text[:160],
                "scaffold_turns": len(episode.lcs.scaffold_sequence),
                "annotation_method": episode.annotation_metadata.method,
                "human_verification_status": episode.annotation_metadata.human_verification_status,
            }
        )
    return summaries


def get_episode(episode_id: str) -> EpisodeRecord:
    for episode in load_demo_episodes():
        if episode.episode_id == episode_id:
            return episode
    raise EpisodeNotFoundError(episode_id)


def public_episode_detail(episode: EpisodeRecord) -> dict[str, object]:
    return {
        "episode_id": episode.episode_id,
        "intervention_id": episode.intervention_id,
        "question_id": episode.question_id,
        "source_split": episode.source_split,
        "subject": episode.subject,
        "topic": episode.topic,
        "problem": episode.problem.model_dump(),
        "annotation_metadata": episode.annotation_metadata.model_dump(),
        "lcs": {
            "kc_components": [item.model_dump() for item in episode.lcs.kc_components],
            "scaffold_sequence": [item.model_dump() for item in episode.lcs.scaffold_sequence],
            "scs": episode.lcs.scs.model_dump(),
        },
    }
