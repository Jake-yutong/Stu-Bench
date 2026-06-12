import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.data.schemas import EpisodeRecord


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def test_episode_record_validates_tiny_fixture():
    payload = json.loads(FIXTURE.read_text())
    episode = EpisodeRecord.model_validate(payload)
    assert episode.episode_id == "demo-001"
    assert episode.lcs.scs.visible_learner_profile.startswith("A Year 7")
    assert episode.lcs.ecs.ground_truth_answer == "C"


def test_scs_rejects_ground_truth_answer_leakage():
    payload = json.loads(FIXTURE.read_text())
    payload["lcs"]["scs"]["ground_truth_answer"] = "C"
    with pytest.raises(ValidationError):
        EpisodeRecord.model_validate(payload)
