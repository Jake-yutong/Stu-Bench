from backend.app.data.schemas import (
    EpisodeRecord,
    EpisodeResult,
    GeneratedTurn,
    ProviderConfig,
    TestMode,
)
from backend.app.services.prompt_service import build_student_messages
from backend.app.services.provider_adapter import ProviderError, chat_completion


async def run_episode(
    episode: EpisodeRecord,
    mode: TestMode,
    student_provider: ProviderConfig,
) -> EpisodeResult:
    history: list[GeneratedTurn] = []
    try:
        for index, scaffold in enumerate(episode.lcs.scaffold_sequence, start=1):
            messages = build_student_messages(episode, mode, history, scaffold.message)
            student_response = await chat_completion(student_provider, messages)
            history.append(
                GeneratedTurn(
                    turn_index=index,
                    tutor_message=scaffold.message,
                    student_response=student_response,
                )
            )
        return EpisodeResult(
            episode_id=episode.episode_id,
            mode=mode,
            status="succeeded",
            generated_trajectory=history,
        )
    except ProviderError as exc:
        return EpisodeResult(
            episode_id=episode.episode_id,
            mode=mode,
            status="failed",
            generated_trajectory=history,
            error_message=str(exc),
        )
