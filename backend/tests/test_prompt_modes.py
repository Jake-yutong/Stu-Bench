import json
from pathlib import Path

import pytest

from backend.app.data.schemas import EpisodeRecord, TestMode as Mode
from backend.app.services.prompt_service import build_student_messages


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def _episode() -> EpisodeRecord:
    return EpisodeRecord.model_validate(json.loads(FIXTURE.read_text()))


@pytest.mark.parametrize("mode", [Mode.roleplay, Mode.profile, Mode.context_engineered])
def test_prompts_exclude_evaluator_leakage(mode: Mode):
    messages = build_student_messages(_episode(), mode, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "ground_truth_answer" not in joined
    assert "real_student_trajectory" not in joined
    assert "reference_kc_transitions" not in joined
    assert "misconception_path" not in joined
    assert "uptake_evidence" not in joined
    assert "evaluation_rubric" not in joined
    assert "Confuses decimal place inspected during rounding." not in joined
    assert "Student should revise based on digit inspection prompt." not in joined


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


def test_invalid_mode_raises_value_error():
    with pytest.raises(ValueError, match="Unknown test mode"):
        build_student_messages(_episode(), "invalid-mode", [], "Tutor hint")
