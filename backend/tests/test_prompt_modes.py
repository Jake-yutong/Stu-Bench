import json
from pathlib import Path

from backend.app.data.schemas import EpisodeRecord, TestMode
from backend.app.services.prompt_service import build_student_messages


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def _episode() -> EpisodeRecord:
    return EpisodeRecord.model_validate(json.loads(FIXTURE.read_text()))


def test_roleplay_prompt_excludes_profile_and_ecs():
    messages = build_student_messages(_episode(), TestMode.roleplay, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "You are simulating a student" in joined
    assert "ground_truth_answer" not in joined
    assert "evaluation_rubric" not in joined
    assert "visible_learner_profile" not in joined


def test_profile_prompt_includes_static_profile_but_not_ecs():
    messages = build_student_messages(_episode(), TestMode.profile, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "Visible learner profile" in joined
    assert "A Year 7 learner" in joined
    assert "ground_truth_answer" not in joined


def test_context_engineered_prompt_includes_scs_and_current_scaffold():
    messages = build_student_messages(_episode(), TestMode.context_engineered, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "Student-facing Context Set" in joined
    assert "Tutor hint" in joined
    assert "ground_truth_answer" not in joined
