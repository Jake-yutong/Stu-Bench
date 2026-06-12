from fastapi import APIRouter, HTTPException

from backend.app.data.schemas import ProviderConfig
from backend.app.services.provider_adapter import ProviderError, chat_completion

router = APIRouter()


@router.post("/test")
async def test_provider(config: ProviderConfig) -> dict[str, object]:
    try:
        text = await chat_completion(
            config,
            [{"role": "user", "content": "Reply with exactly: connection ok"}],
        )
    except ProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "sample": text[:200]}
