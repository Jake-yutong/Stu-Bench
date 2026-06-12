from backend.app.data.schemas import EpisodeRecord, GeneratedTurn, TestMode


ChatMessage = dict[str, str]


def _problem_block(episode: EpisodeRecord) -> str:
    options = "\n".join(
        f"{option.label}. {option.text}" for option in episode.problem.answer_options
    )
    return f"Problem:\n{episode.problem.text}\n\nAnswer options:\n{options}"


def _history_block(history: list[GeneratedTurn]) -> str:
    if not history:
        return "No previous generated turns in this episode."
    return "\n".join(
        f"Turn {turn.turn_index}\nTutor: {turn.tutor_message}\nStudent: {turn.student_response}"
        for turn in history
    )


def build_student_messages(
    episode: EpisodeRecord,
    mode: TestMode,
    history: list[GeneratedTurn],
    current_scaffold: str,
) -> list[ChatMessage]:
    system = (
        "You are simulating a lower-secondary mathematics student in a tutoring dialogue. "
        "Respond as the student only. Keep responses brief and natural. Do not reveal hidden evaluation logic."
    )
    problem = _problem_block(episode)
    history_text = _history_block(history)

    if mode == TestMode.roleplay:
        user = (
            f"{problem}\n\n"
            "You are simulating a student. Answer the tutor's next message as that student.\n\n"
            f"Episode history:\n{history_text}\n\n"
            f"Tutor message:\n{current_scaffold}"
        )
    elif mode == TestMode.profile:
        scs = episode.lcs.scs
        user = (
            f"{problem}\n\n"
            f"Visible learner profile: {scs.visible_learner_profile}\n"
            f"Initial learner state: {scs.initial_learner_state}\n"
            f"Current confusion: {scs.current_confusion}\n"
            f"Language style: {scs.language_style}\n\n"
            f"Episode history:\n{history_text}\n\n"
            f"Tutor message:\n{current_scaffold}"
        )
    else:
        scs = episode.lcs.scs
        kc_states = ", ".join(
            f"{item.kc_id}={item.state}" for item in scs.kc_state_abstraction
        )
        user = (
            f"{problem}\n\n"
            "Student-facing Context Set:\n"
            f"- Visible learner profile: {scs.visible_learner_profile}\n"
            f"- Initial learner state: {scs.initial_learner_state}\n"
            f"- Current confusion: {scs.current_confusion}\n"
            f"- Language style: {scs.language_style}\n"
            f"- KC state abstraction: {kc_states}\n\n"
            f"Episode history:\n{history_text}\n\n"
            f"Current tutor scaffold:\n{current_scaffold}\n\n"
            "Generate one student response only. Show plausible uptake only when the scaffold supports it."
        )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
