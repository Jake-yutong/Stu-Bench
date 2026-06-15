import json

from backend.app.data.schemas import EpisodeRecord, EpisodeResult, ProviderConfig
from backend.app.services.judge_normalizer import load_judge_payload, normalize_judge_scores
from backend.app.services.provider_adapter import ProviderError, chat_completion


def build_judge_messages(episode: EpisodeRecord, result: EpisodeResult) -> list[dict[str, str]]:
    trajectory = [turn.model_dump() for turn in result.generated_trajectory]
    evaluator_context = episode.lcs.ecs.model_dump()
    rubric = (
        "Evaluate learner realism using the Stu-Bench paper metrics. "
        "Return only JSON. Score these 0-100 fields: overall_realism, "
        "initial_state_fidelity, mistake_authenticity, scaffolding_uptake, "
        "kc_transition_consistency, learning_trajectory_plausibility, "
        "over_competence_control. Higher is better for all displayed scores; "
        "over_competence_control is higher when the model avoids expert-like leaps. "
        "Also return formula_metrics with kts, uptake, over_improve, and status. "
        "Use KTS = 1 - mean absolute delta difference between LLM and human KC transitions, "
        "Uptake = mean I(u_t=1) over scaffold turns, and OverImprove = mean I(o_t=1) "
        "over scaffold turns. kts, uptake, and over_improve must be ratios in [0,1]. "
        "Set formula_metrics.status to computed only when these values are computed from "
        "structured annotations; otherwise use judge_estimated for LLM-as-judge estimates "
        "or pending_annotation when no estimate is justified. Include judge_rationale and "
        "failure_flags."
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
        scores = normalize_judge_scores(load_judge_payload(text))
        return result.model_copy(update={"judge_scores": scores})
    except (ProviderError, json.JSONDecodeError, ValueError) as exc:
        return result.model_copy(update={"status": "failed", "error_message": f"Judge failed: {exc}"})
