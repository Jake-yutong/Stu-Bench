import asyncio
import json
from pathlib import Path

import pytest

from backend.app.data.schemas import (
    EpisodeRecord,
    EpisodeResult,
    ProviderConfig,
    ProviderPreset,
    RunConfig,
    TestMode as Mode,
)
from backend.app.services.run_manager import get_run_status, reset_run_state, start_run


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def _episode() -> EpisodeRecord:
    return EpisodeRecord.model_validate(json.loads(FIXTURE.read_text()))


def _mock_provider(model: str) -> ProviderConfig:
    return ProviderConfig(
        preset=ProviderPreset.mock,
        base_url="mock://local",
        api_key="mock",
        model=model,
        temperature=0.4,
    )


@pytest.mark.anyio
async def test_batch_run_executes_each_episode_for_each_mode():
    reset_run_state()
    config = RunConfig(
        modes=[Mode.roleplay, Mode.context_engineered, Mode.no_kc_scs],
        student_provider=_mock_provider("mock-student"),
        judge_provider=_mock_provider("mock-judge"),
        episode_ids=["tiny-episode"],
    )

    status = start_run(config, [_episode()])
    assert status["total"] == 3

    for _ in range(50):
        status = get_run_status(status["run_id"])
        if status["status"] == "completed":
            break
        await asyncio.sleep(0.05)

    assert status["status"] == "completed"
    assert status["completed"] == 3
    result_modes = [item["mode"] for item in status["results"]]
    assert result_modes == ["roleplay", "context_engineered", "no_kc_scs"]


@pytest.mark.anyio
async def test_batch_run_marks_timed_out_condition_failed_and_keeps_progress(monkeypatch):
    reset_run_state()

    async def slow_run_episode(episode, mode, student_provider):
        await asyncio.sleep(1)
        return EpisodeResult(
            episode_id=episode.episode_id,
            mode=mode,
            status="succeeded",
        )

    monkeypatch.setattr("backend.app.services.run_manager.run_episode", slow_run_episode)
    monkeypatch.setattr("backend.app.services.run_manager.EPISODE_CONDITION_TIMEOUT_SECONDS", 0.01)
    config = RunConfig(
        modes=[Mode.roleplay, Mode.context_engineered],
        student_provider=_mock_provider("mock-student"),
        judge_provider=_mock_provider("mock-judge"),
        episode_ids=["tiny-episode"],
    )

    status = start_run(config, [_episode()])
    assert status["total"] == 2

    for _ in range(50):
        status = get_run_status(status["run_id"])
        if status["status"] == "completed":
            break
        await asyncio.sleep(0.02)

    assert status["status"] == "completed"
    assert status["completed"] == 2
    assert [item["status"] for item in status["results"]] == ["failed", "failed"]
    assert all("timed out" in item["error_message"] for item in status["results"])
