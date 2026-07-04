import json
from pathlib import Path

import pytest

from backend.app.data.schemas import (
    EpisodeRecord,
    ProviderConfig,
    ProviderPreset,
    ScaffoldTurn,
    TestMode as Mode,
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


def _prompt_text(messages: list[dict[str, str]]) -> str:
    return "\n".join(message["content"] for message in messages)


@pytest.mark.anyio
async def test_run_episode_calls_student_once_per_scaffold_turn(monkeypatch):
    episode = _two_turn_episode()
    calls = 0

    async def fake_chat_completion(config, messages, **kwargs):
        nonlocal calls
        calls += 1
        return f"student response {calls}"

    monkeypatch.setattr("backend.app.services.runner.chat_completion", fake_chat_completion)

    result = await run_episode(episode, Mode.roleplay, _mock_provider())

    assert result.status == "succeeded"
    assert len(result.generated_trajectory) == len(episode.lcs.scaffold_sequence)
    assert calls == len(episode.lcs.scaffold_sequence)


@pytest.mark.anyio
async def test_run_episode_passes_progressive_history_into_prompts(monkeypatch):
    episode = _two_turn_episode()
    captured_messages = []
    responses = ["student-turn-one-marker", "student-turn-two-marker"]

    async def fake_chat_completion(config, messages, **kwargs):
        captured_messages.append(messages)
        return responses[len(captured_messages) - 1]

    monkeypatch.setattr("backend.app.services.runner.chat_completion", fake_chat_completion)

    result = await run_episode(episode, Mode.profile, _mock_provider())

    second_prompt = _prompt_text(captured_messages[1])
    assert result.status == "succeeded"
    assert episode.lcs.scaffold_sequence[0].message in second_prompt
    assert "student-turn-one-marker" in second_prompt


@pytest.mark.anyio
async def test_run_episode_starts_with_clean_history_each_time(monkeypatch):
    episode = _two_turn_episode()
    captured_messages = []
    responses = [
        "first-run-first-response-marker",
        "first-run-second-response",
        "second-run-first-response",
        "second-run-second-response",
    ]

    async def fake_chat_completion(config, messages, **kwargs):
        captured_messages.append(messages)
        return responses[len(captured_messages) - 1]

    monkeypatch.setattr("backend.app.services.runner.chat_completion", fake_chat_completion)

    first = await run_episode(episode, Mode.context_engineered, _mock_provider())
    second = await run_episode(episode, Mode.context_engineered, _mock_provider())

    assert first.generated_trajectory[0].turn_index == 1
    assert second.generated_trajectory[0].turn_index == 1
    second_run_first_prompt = _prompt_text(captured_messages[2])
    assert "first-run-first-response-marker" not in second_run_first_prompt


@pytest.mark.anyio
async def test_run_episode_returns_failed_result_with_partial_trajectory(monkeypatch):
    episode = _two_turn_episode()
    calls = 0

    async def fake_chat_completion(config, messages, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ProviderError("provider stopped on turn 2")
        return "I would look at the 5 after the decimal."

    monkeypatch.setattr("backend.app.services.runner.chat_completion", fake_chat_completion)

    result = await run_episode(episode, Mode.context_engineered, _mock_provider())

    assert result.status == "failed"
    assert len(result.generated_trajectory) == 1
    assert result.generated_trajectory[0].turn_index == 1
    assert result.error_message == "provider stopped on turn 2"


@pytest.mark.anyio
async def test_run_episode_preserves_no_kc_scs_mode(monkeypatch):
    episode = _episode()

    async def fake_chat_completion(config, messages, **kwargs):
        joined = _prompt_text(messages)
        assert "KC state abstraction" not in joined
        return "I am not sure yet."

    monkeypatch.setattr("backend.app.services.runner.chat_completion", fake_chat_completion)

    result = await run_episode(episode, Mode.no_kc_scs, _mock_provider())

    assert result.status == "succeeded"
    assert result.mode == Mode.no_kc_scs


@pytest.mark.anyio
async def test_run_episode_limits_student_reply_tokens(monkeypatch):
    episode = _episode()
    captured_max_tokens = []

    async def fake_chat_completion(config, messages, **kwargs):
        captured_max_tokens.append(kwargs.get("max_tokens"))
        return "Short unsure student reply."

    monkeypatch.setattr("backend.app.services.runner.chat_completion", fake_chat_completion)

    result = await run_episode(episode, Mode.context_engineered, _mock_provider())

    assert result.status == "succeeded"
    assert captured_max_tokens == [180]
