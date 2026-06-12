from pathlib import Path

import pandas as pd
import pytest

from backend.scripts.prepare_demo_episodes import build_episode_record, prepare, select_episode_ids


def test_select_episode_ids_prefers_dialogues_with_minimum_turns():
    short_dialogue = [
        {"InterventionId": 1, "QuestionId_DQ": 101, "MessageSequence": 1, "IsTutor": 1, "MessageString": "a", "TalkMovePrediction": "<None>"},
        {"InterventionId": 1, "QuestionId_DQ": 101, "MessageSequence": 2, "IsTutor": 0, "MessageString": "b", "TalkMovePrediction": None},
    ]
    long_dialogue = [
        {"InterventionId": 2, "QuestionId_DQ": 202, "MessageSequence": i, "IsTutor": i % 2, "MessageString": f"m{i}", "TalkMovePrediction": "hint"}
        for i in range(1, 13)
    ]
    dialogues = pd.DataFrame(short_dialogue + long_dialogue)
    selected = select_episode_ids(dialogues, count=1, min_turns=10)
    assert selected == [(2, 202)]


def test_build_episode_record_splits_scs_and_ecs():
    dialogue_rows = pd.DataFrame(
        [
            {"InterventionId": 10, "QuestionId_DQ": 104614, "MessageSequence": 1, "IsTutor": 1, "MessageString": "Tutor prompt", "TalkMovePrediction": "<None>"},
            {"InterventionId": 10, "QuestionId_DQ": 104614, "MessageSequence": 2, "IsTutor": 0, "MessageString": "Student answer", "TalkMovePrediction": None}
        ]
    )
    metadata = pd.DataFrame(
        [
            {"QuestionId_DQ": 104614, "InterventionId": 10, "Text": "Question text", "Sequence": 1, "Label": "Question Text"},
            {"QuestionId_DQ": 104614, "InterventionId": 10, "Text": "Only Alex", "Sequence": 2, "Label": "Answer A Text"},
            {"QuestionId_DQ": 104614, "InterventionId": 10, "Text": "Both", "Sequence": 4, "Label": "Answer C Text"}
        ]
    )
    subjects = pd.DataFrame(
        [
            {"InterventionId": 10, "SubjectName": "Number", "SubjectLevel": 1, "SubjectType": "Subject"},
            {"InterventionId": 10, "SubjectName": "Rounding", "SubjectLevel": 2, "SubjectType": "Topic"}
        ]
    )
    episode = build_episode_record((10, 104614), dialogue_rows, metadata, subjects)
    assert episode.lcs.scs.visible_learner_profile
    assert episode.lcs.ecs.real_student_trajectory[1].speaker == "student"
    assert "ground_truth_answer" not in episode.lcs.scs.model_dump()
    assert episode.lcs.scaffold_sequence[0].type == "tutor_message"


def test_build_episode_record_normalizes_missing_text_fields():
    dialogue_rows = pd.DataFrame(
        [
            {"InterventionId": 11, "QuestionId_DQ": 104615, "MessageSequence": 1, "IsTutor": 1, "MessageString": None, "TalkMovePrediction": "questioning"},
            {"InterventionId": 11, "QuestionId_DQ": 104615, "MessageSequence": 2, "IsTutor": 0, "MessageString": None, "TalkMovePrediction": None}
        ]
    )
    metadata = pd.DataFrame(
        [
            {"QuestionId_DQ": 104615, "InterventionId": 11, "Text": None, "Sequence": 1, "Label": "Question Text"},
            {"QuestionId_DQ": 104615, "InterventionId": 11, "Text": None, "Sequence": 2, "Label": "Answer A Text"},
        ]
    )
    subjects = pd.DataFrame(
        [
            {"InterventionId": 11, "SubjectName": None, "SubjectLevel": 1, "SubjectType": "Subject"},
        ]
    )
    episode = build_episode_record((11, 104615), dialogue_rows, metadata, subjects)
    assert episode.problem.text == "Question text unavailable"
    assert episode.problem.answer_options[0].text == ""
    assert episode.lcs.ecs.real_student_trajectory[0].message == ""
    assert "nan" not in episode.model_dump_json()


def test_prepare_raises_when_not_enough_eligible_episodes(tmp_path: Path):
    input_dir = tmp_path / "dataset"
    anchored_dir = input_dir / "anchored-dialogues"
    anchored_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {"InterventionId": 1, "QuestionId_DQ": 101, "MessageSequence": 1, "IsTutor": 1, "MessageString": "a", "TalkMovePrediction": "hint"},
            {"InterventionId": 1, "QuestionId_DQ": 101, "MessageSequence": 2, "IsTutor": 0, "MessageString": "b", "TalkMovePrediction": None},
            {"InterventionId": 2, "QuestionId_DQ": 202, "MessageSequence": 1, "IsTutor": 1, "MessageString": "c", "TalkMovePrediction": "hint"},
        ]
    ).to_csv(anchored_dir / "train.csv", index=False)
    pd.DataFrame(
        [
            {"QuestionId_DQ": 202, "InterventionId": 2, "Text": "Question text", "Sequence": 1, "Label": "Question Text"},
        ]
    ).to_csv(input_dir / "dq-question-metadata.csv", index=False)
    pd.DataFrame(
        [
            {"InterventionId": 2, "SubjectName": "Number", "SubjectLevel": 1, "SubjectType": "Subject"},
        ]
    ).to_csv(input_dir / "dialogue-subjects.csv", index=False)

    output_path = tmp_path / "out.json"

    with pytest.raises(ValueError, match="Expected 2 episodes but only found 1 eligible"):
        prepare(input_dir, output_path, count=2, min_turns=2)

    assert not output_path.exists()
