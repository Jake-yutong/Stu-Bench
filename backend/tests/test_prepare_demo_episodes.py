import pandas as pd

from backend.scripts.prepare_demo_episodes import build_episode_record, select_episode_ids


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
            {"InterventionId": 10, "QuestionId_DQ": 104614, "MessageSequence": 1, "IsTutor": 1, "MessageString": "Tutor prompt", "TalkMovePrediction": "questioning"},
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
