import pytest

from backend.app.data.schemas import ProviderConfig, ProviderPreset
from backend.app.services.provider_adapter import chat_completion, provider_base_url


def test_provider_presets_resolve_base_urls():
    assert provider_base_url(ProviderPreset.openai) == "https://api.openai.com/v1"
    assert provider_base_url(ProviderPreset.deepseek) == "https://api.deepseek.com"
    assert provider_base_url(ProviderPreset.qwen) == "https://dashscope.aliyuncs.com/compatible-mode/v1"


@pytest.mark.anyio
async def test_mock_provider_returns_deterministic_student_text():
    config = ProviderConfig(
        preset=ProviderPreset.mock,
        base_url="mock://local",
        api_key="mock",
        model="mock-student",
        temperature=0.4,
    )
    text = await chat_completion(config, [{"role": "user", "content": "Tutor message: Try rounding."}])
    assert "I think" in text
