import json
from pathlib import Path
from collections.abc import Iterator

import pytest

from backend.app.data.schemas import EpisodeRecord, TestMode as Mode
from backend.app.services.prompt_service import build_student_messages


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def _episode() -> EpisodeRecord:
    return EpisodeRecord.model_validate(json.loads(FIXTURE.read_text()))


def _ecs_scalar_values(payload: object) -> Iterator[str]:
    if payload is None:
        return
    if isinstance(payload, dict):
        for value in payload.values():
            yield from _ecs_scalar_values(value)
        return
    if isinstance(payload, list):
        for value in payload:
            yield from _ecs_scalar_values(value)
        return
    if isinstance(payload, (str, int, float)):
        text = str(payload)
        if text:
            yield text


def _assert_ecs_values_absent(mode: Mode, joined: str) -> None:
    ecs_payload = _episode().lcs.ecs.model_dump()
    # Tiny allowlist for benign overlaps with visible prompt text:
    # - "student" appears in the roleplay/system wording
    # - "tutor" appears in "tutoring dialogue" and "Tutor hint"
    # - "C" appears in the public answer options
    # - "1" appears in the shared "1 decimal place" scaffold text
    # - "kc-rounding-place-value" appears in the visible KC abstraction for profile/context-engineered modes
    allowlist = {"student", "tutor", "1", "C", "kc-rounding-place-value"}
    for value in _ecs_scalar_values(ecs_payload):
        if value in allowlist:
            continue
        assert value not in joined, f"{mode.value} prompt leaked ECS scalar value: {value!r}"


@pytest.mark.parametrize("mode", [Mode.roleplay, Mode.profile, Mode.context_engineered, Mode.no_kc_scs])
def test_prompts_exclude_evaluator_leakage(mode: Mode):
    messages = build_student_messages(_episode(), mode, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    ecs_fields = (
        "ground_truth_answer",
        "real_student_trajectory",
        "reference_kc_transitions",
        "misconception_path",
        "uptake_evidence",
        "evaluation_rubric",
    )
    for field_name in ecs_fields:
        assert field_name not in joined
    _assert_ecs_values_absent(mode, joined)


def test_roleplay_prompt_excludes_profile_and_ecs():
    messages = build_student_messages(_episode(), Mode.roleplay, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "You are simulating a student" in joined
    assert "visible_learner_profile" not in joined


def test_profile_prompt_includes_static_profile_but_not_ecs():
    messages = build_student_messages(_episode(), Mode.profile, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "Visible learner profile" in joined
    assert "A Year 7 learner" in joined
    assert "ground_truth_answer" not in joined


def test_context_engineered_prompt_includes_scs_and_current_scaffold():
    messages = build_student_messages(_episode(), Mode.context_engineered, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "Student-facing Context Set" in joined
    assert "Tutor hint" in joined
    assert "ground_truth_answer" not in joined


def test_no_kc_scs_prompt_includes_scs_without_kc_state():
    messages = build_student_messages(_episode(), Mode.no_kc_scs, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "Student-facing Context Set" in joined
    assert "Tutor hint" in joined
    assert "KC state abstraction" not in joined
    assert "kc-rounding-place-value" not in joined
    assert "ground_truth_answer" not in joined


def test_invalid_mode_raises_value_error():
    with pytest.raises(ValueError, match="Unknown test mode"):
        build_student_messages(_episode(), "invalid-mode", [], "Tutor hint")
