import json
from pathlib import Path

import pytest

from backend.app.data.schemas import (
    EpisodeRecord,
    ProviderConfig,
    ProviderPreset,
    ScaffoldTurn,
    TestMode,
)
from backend.app.services.provider_adapter import ProviderError
from backend.app.services.runner import run_episode


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def _episode() -> EpisodeRecord:
    return EpisodeRecord.model_validate(json.loads(FIXTURE.read_text()))


def _two_turn_episode() -> EpisodeRecord:
    episode = _episode()
    scaffolds = [
        *episode.lcs.scaffold_sequence,
        ScaffoldTurn(
            turn_id="t2",
            type="questioning",
            support_level=2,
            message="Now should we round up or stay at 5.4?",
        ),
    ]
    return episode.model_copy(
        deep=True,
        update={"lcs": episode.lcs.model_copy(update={"scaffold_sequence": scaffolds})},
    )


def _mock_provider() -> ProviderConfig:
    return ProviderConfig(
        preset=ProviderPreset.mock,
        base_url="mock://local",
        api_key="mock",
        model="mock-student",
        temperature=0.4,
    )


@pytest.mark.anyio
async def test_run_episode_calls_student_once_per_scaffold_turn(monkeypatch):
    episode = _two_turn_episode()
    calls = 0

    async def fake_chat_completion(config, messages):
        nonlocal calls
        calls += 1
        return f"student response {calls}"

    monkeypatch.setattr("backend.app.services.runner.chat_completion", fake_chat_completion)

    result = await run_episode(episode, TestMode.roleplay, _mock_provider())

    assert result.status == "succeeded"
    assert len(result.generated_trajectory) == len(episode.lcs.scaffold_sequence)
    assert calls == len(episode.lcs.scaffold_sequence)


@pytest.mark.anyio
async def test_run_episode_starts_with_clean_history_each_time():
    episode = _episode()

    first = await run_episode(episode, TestMode.profile, _mock_provider())
    second = await run_episode(episode, TestMode.profile, _mock_provider())

    assert first.generated_trajectory[0].turn_index == 1
    assert second.generated_trajectory[0].turn_index == 1


@pytest.mark.anyio
async def test_run_episode_returns_failed_result_with_partial_trajectory(monkeypatch):
    episode = _two_turn_episode()
    calls = 0

    async def fake_chat_completion(config, messages):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ProviderError("provider stopped on turn 2")
        return "I would look at the 5 after the decimal."

    monkeypatch.setattr("backend.app.services.runner.chat_completion", fake_chat_completion)

    result = await run_episode(episode, TestMode.context_engineered, _mock_provider())

    assert result.status == "failed"
    assert len(result.generated_trajectory) == 1
    assert result.generated_trajectory[0].turn_index == 1
    assert result.error_message == "provider stopped on turn 2"
