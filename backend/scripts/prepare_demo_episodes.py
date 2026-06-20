import argparse
import json
import sys
from pathlib import Path

import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.data.schemas import (
    AnswerOption,
    DialogueTurn,
    EpisodeRecord,
    EvaluatorFacingContext,
    KCComponent,
    KCStateAbstraction,
    LearnerContextSet,
    Problem,
    ScaffoldTurn,
    StudentFacingContext,
)


ANSWER_LABELS = {
    "Answer A Text": "A",
    "Answer B Text": "B",
    "Answer C Text": "C",
    "Answer D Text": "D",
}


def _clean_text(value: object, fallback: str = "") -> str:
    if pd.isna(value):
        return fallback
    text = str(value).strip()
    if text.lower() in {"nan", "none", "<none>"}:
        return fallback
    return text


def _scaffold_type(value: object) -> str:
    cleaned = _clean_text(value)
    return cleaned if cleaned else "tutor_message"


def select_episode_ids(dialogues: pd.DataFrame, count: int, min_turns: int) -> list[tuple[int, int]]:
    grouped = (
        dialogues.groupby(["InterventionId", "QuestionId_DQ"])
        .size()
        .reset_index(name="turn_count")
        .sort_values(["turn_count", "InterventionId", "QuestionId_DQ"], ascending=[False, True, True])
    )
    eligible = grouped[grouped["turn_count"] >= min_turns].head(count)
    return [(int(row.InterventionId), int(row.QuestionId_DQ)) for row in eligible.itertuples()]


def _question_text(metadata_rows: pd.DataFrame) -> str:
    matches = metadata_rows[metadata_rows["Label"] == "Question Text"].sort_values("Sequence")
    return _clean_text(matches.iloc[0]["Text"], fallback="Question text unavailable") if not matches.empty else "Question text unavailable"


def _answer_options(metadata_rows: pd.DataFrame) -> list[AnswerOption]:
    options: list[AnswerOption] = []
    for row in metadata_rows.sort_values("Sequence").itertuples():
        label = ANSWER_LABELS.get(str(row.Label))
        if label:
            options.append(AnswerOption(label=label, text=_clean_text(row.Text)))
    return options


def _subject_topic(subject_rows: pd.DataFrame) -> tuple[str | None, str | None]:
    subject = None
    topic = None
    for row in subject_rows.sort_values("SubjectLevel").itertuples():
        if row.SubjectType == "Subject" and subject is None:
            subject = _clean_text(row.SubjectName)
        if row.SubjectType == "Topic" and topic is None:
            topic = _clean_text(row.SubjectName)
    return subject, topic


def build_episode_record(
    key: tuple[int, int],
    dialogue_rows: pd.DataFrame,
    metadata: pd.DataFrame,
    subjects: pd.DataFrame,
    source_split: str = "test",
) -> EpisodeRecord:
    intervention_id, question_id = key
    rows = dialogue_rows[
        (dialogue_rows["InterventionId"] == intervention_id)
        & (dialogue_rows["QuestionId_DQ"] == question_id)
    ].sort_values("MessageSequence")
    metadata_rows = metadata[
        (metadata["InterventionId"] == intervention_id)
        & (metadata["QuestionId_DQ"] == question_id)
    ]
    subject_rows = subjects[subjects["InterventionId"] == intervention_id]
    subject, topic = _subject_topic(subject_rows)
    dialogue = [
        DialogueTurn(
            turn_index=int(row.MessageSequence),
            speaker="tutor" if int(row.IsTutor) == 1 else "student",
            message=_clean_text(row.MessageString),
        )
        for row in rows.itertuples()
    ]
    scaffold = [
        ScaffoldTurn(
            turn_id=f"t{idx + 1}",
            type=_scaffold_type(row.TalkMovePrediction),
            support_level=1 if int(row.IsTutor) == 1 else 0,
            message=_clean_text(row.MessageString),
        )
        for idx, row in enumerate(rows[rows["IsTutor"] == 1].itertuples())
    ]
    topic_text = topic or subject or "mathematics"
    kc_id = f"kc-{topic_text.lower().replace(' ', '-')}"
    lcs = LearnerContextSet(
        kc_components=[KCComponent(id=kc_id, description=f"Reason about {topic_text}")],
        scaffold_sequence=scaffold[:8],
        scs=StudentFacingContext(
            visible_learner_profile="A lower-secondary learner responding in a brief, tentative style.",
            initial_learner_state="Derived from the beginning of a real tutoring episode; the learner may hold a partial or confused understanding.",
            current_confusion=f"Likely confusion connected to {topic_text}.",
            language_style="Short, natural student replies; avoid expert explanations unless scaffolded.",
            kc_state_abstraction=[KCStateAbstraction(kc_id=kc_id, state="partial")],
        ),
        ecs=EvaluatorFacingContext(
            ground_truth_answer="pending_annotation",
            real_student_trajectory=dialogue,
            reference_kc_transitions=[],
            misconception_path=f"Judge should infer misconception path from the real trajectory and {topic_text} context.",
            uptake_evidence="Use the real student trajectory and tutor scaffolds as reference evidence.",
            evaluation_rubric="Reward gradual, scaffold-linked learner realism. Penalize over-competence, irrelevant uptake, and mechanical agreement.",
        ),
    )
    return EpisodeRecord(
        episode_id=f"eedi-{intervention_id}-{question_id}",
        intervention_id=intervention_id,
        question_id=question_id,
        source_split=source_split,
        subject=subject,
        topic=topic,
        problem=Problem(text=_question_text(metadata_rows), answer_options=_answer_options(metadata_rows)),
        lcs=lcs,
    )


def prepare(
    input_dir: Path,
    output_path: Path,
    count: int = 20,
    min_turns: int = 10,
    split: str = "test",
) -> list[EpisodeRecord]:
    if split not in {"test", "val", "train"}:
        raise ValueError("split must be one of: test, val, train")
    dialogues = pd.read_csv(input_dir / "anchored-dialogues" / f"{split}.csv")
    metadata = pd.read_csv(input_dir / "dq-question-metadata.csv")
    subjects = pd.read_csv(input_dir / "dialogue-subjects.csv")
    keys = select_episode_ids(dialogues, count=count, min_turns=min_turns)
    episodes = [build_episode_record(key, dialogues, metadata, subjects, split) for key in keys]
    if len(episodes) != count:
        raise ValueError(f"Expected {count} episodes but only found {len(episodes)} eligible")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps([episode.model_dump() for episode in episodes], indent=2))
    return episodes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--min-turns", type=int, default=10)
    parser.add_argument("--split", choices=["test", "val", "train"], default="test")
    args = parser.parse_args()
    episodes = prepare(Path(args.input_dir), Path(args.output), args.count, args.min_turns, args.split)
    print(f"Wrote {len(episodes)} episodes to {args.output}")


if __name__ == "__main__":
    main()
