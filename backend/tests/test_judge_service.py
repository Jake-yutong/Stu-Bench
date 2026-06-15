import json
from pathlib import Path

import pytest

from backend.app.data.schemas import EpisodeRecord, ProviderConfig, ProviderPreset, TestMode as Mode
from backend.app.services.judge_service import build_judge_messages, judge_episode
from backend.app.services.judge_normalizer import normalize_judge_scores
from backend.app.services.runner import run_episode


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def _episode() -> EpisodeRecord:
    return EpisodeRecord.model_validate(json.loads(FIXTURE.read_text()))


def _provider(model: str = "mock-judge") -> ProviderConfig:
    return ProviderConfig(
        preset=ProviderPreset.mock,
        base_url="mock://local",
        api_key="mock",
        model=model,
        temperature=0.0,
    )


@pytest.mark.anyio
async def test_judge_episode_returns_scores_on_0_to_100_scale():
    episode = _episode()
    result = await run_episode(episode, Mode.context_engineered, _provider("mock-student"))

    judged = await judge_episode(episode, result, _provider())

    assert judged.judge_scores is not None
    assert judged.judge_scores.overall_realism == 78
    assert judged.judge_scores.over_competence_control == 83
    assert judged.judge_scores.formula_metrics.status == "judge_estimated"
    assert judged.judge_scores.formula_metrics.uptake is None


@pytest.mark.anyio
async def test_build_judge_messages_include_ecs_and_generated_trajectory():
    episode = _episode()
    result = await run_episode(episode, Mode.context_engineered, _provider("mock-student"))

    messages = build_judge_messages(episode, result)
    prompt_text = "\n".join(message["content"] for message in messages)

    assert episode.lcs.ecs.ground_truth_answer in prompt_text
    assert episode.lcs.ecs.real_student_trajectory[0].message in prompt_text
    assert result.generated_trajectory[0].student_response in prompt_text
    assert "formula_metrics.status" in prompt_text


@pytest.mark.anyio
async def test_judge_episode_fails_when_judge_returns_invalid_json(monkeypatch):
    episode = _episode()
    result = await run_episode(episode, Mode.context_engineered, _provider("mock-student"))

    async def fake_chat_completion(config, messages):
        return "not json"

    monkeypatch.setattr("backend.app.services.judge_service.chat_completion", fake_chat_completion)

    judged = await judge_episode(episode, result, _provider())

    assert judged.status == "failed"
    assert judged.error_message is not None
    assert judged.error_message.startswith("Judge failed:")


@pytest.mark.anyio
async def test_judge_episode_normalizes_real_judge_metric_payload(monkeypatch):
    episode = _episode()
    result = await run_episode(episode, Mode.context_engineered, _provider("mock-student"))

    async def fake_chat_completion(config, messages):
        return json.dumps(
            {
                "scores": {
                    "overall": 0.62,
                    "initialLearnerStateFidelity": 71,
                    "mistakeAuthenticity": None,
                    "learningTrajectoryPlausibility": 75,
                },
                "formula_metrics": {
                    "kts": 0.5,
                    "uptake": 0.75,
                    "over_improvement": 0.25,
                },
                "rationale": "The simulated learner shows partial uptake but improves too quickly.",
            }
        )

    monkeypatch.setattr("backend.app.services.judge_service.chat_completion", fake_chat_completion)

    judged = await judge_episode(episode, result, _provider())

    assert judged.status == "succeeded"
    assert judged.judge_scores is not None
    assert judged.judge_scores.overall_realism == 62
    assert judged.judge_scores.mistake_authenticity == 62
    assert judged.judge_scores.scaffolding_uptake == 75
    assert judged.judge_scores.kc_transition_consistency == 50
    assert judged.judge_scores.over_competence_control == 75
    assert judged.judge_scores.judge_rationale == (
        "The simulated learner shows partial uptake but improves too quickly."
    )
    assert judged.judge_scores.formula_metrics.kts == 0.5
    assert judged.judge_scores.formula_metrics.uptake == 0.75
    assert judged.judge_scores.formula_metrics.over_improve == 0.25
    assert judged.judge_scores.formula_metrics.status == "judge_estimated"


def test_judge_normalizer_maps_common_llm_judge_aliases():
    scores = normalize_judge_scores(
        {
            "learner_realism": 64,
            "uptake_relevance": 72,
            "trajectory_realism": 81,
            "judge_rationale": "Alias-heavy judge output.",
            "formula_metrics": {"status": "judge_estimated"},
        }
    )

    assert scores.overall_realism == 64
    assert scores.scaffolding_uptake == 72
    assert scores.learning_trajectory_plausibility == 81


@pytest.mark.anyio
async def test_judge_episode_skips_failed_episode_result(monkeypatch):
    episode = _episode()
    result = await run_episode(episode, Mode.context_engineered, _provider("mock-student"))
    failed = result.model_copy(update={"status": "failed", "error_message": "student provider failed"})

    async def fake_chat_completion(config, messages):
        raise AssertionError("judge should not be called for failed student result")

    monkeypatch.setattr("backend.app.services.judge_service.chat_completion", fake_chat_completion)

    judged = await judge_episode(episode, failed, _provider())

    assert judged is failed
    assert judged.error_message == "student provider failed"
