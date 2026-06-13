import json

from pydantic import ValidationError

from backend.app.data.schemas import EpisodeRecord, EpisodeResult, JudgeScores, ProviderConfig
from backend.app.services.provider_adapter import ProviderError, chat_completion


def build_judge_messages(episode: EpisodeRecord, result: EpisodeResult) -> list[dict[str, str]]:
    trajectory = [turn.model_dump() for turn in result.generated_trajectory]
    evaluator_context = episode.lcs.ecs.model_dump()
    rubric = (
        "Score each field from 0 to 100. Higher is better. "
        "over_competence_control is higher when the model avoids expert-like leaps. "
        "Return only JSON matching the requested keys, including formula_metrics. "
        "Set formula_metrics.status to judge_estimated unless reliable structured annotations "
        "support computed metrics; use pending_annotation when no estimate is justified."
    )
    return [
        {
            "role": "system",
            "content": (
                "You are an evaluator for learner realism in scaffolded tutoring dialogues."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{rubric}\n\n"
                f"Problem: {json.dumps(episode.problem.model_dump(), ensure_ascii=False)}\n\n"
                "Evaluator-facing context: "
                f"{json.dumps(evaluator_context, ensure_ascii=False)}\n\n"
                f"Generated trajectory: {json.dumps(trajectory, ensure_ascii=False)}"
            ),
        },
    ]


async def judge_episode(
    episode: EpisodeRecord,
    result: EpisodeResult,
    judge_provider: ProviderConfig,
) -> EpisodeResult:
    if result.status == "failed":
        return result
    try:
        text = await chat_completion(judge_provider, build_judge_messages(episode, result))
        scores = JudgeScores.model_validate(json.loads(text))
        return result.model_copy(update={"judge_scores": scores})
    except (ProviderError, json.JSONDecodeError, ValidationError) as exc:
        return result.model_copy(update={"status": "failed", "error_message": f"Judge failed: {exc}"})
