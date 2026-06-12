import pytest
import httpx

from backend.app.data.schemas import ProviderConfig, ProviderPreset
from backend.app.services.provider_adapter import ProviderError, chat_completion, provider_base_url


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


@pytest.mark.anyio
async def test_httpx_request_errors_are_wrapped_as_provider_error(monkeypatch):
    config = ProviderConfig(
        preset=ProviderPreset.openai,
        base_url="https://api.openai.com/v1",
        api_key="secret",
        model="gpt-test",
        temperature=0.4,
    )

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            raise httpx.ConnectError("boom", request=httpx.Request("POST", "https://example.com"))

    monkeypatch.setattr("backend.app.services.provider_adapter.httpx.AsyncClient", FakeClient)

    with pytest.raises(ProviderError, match="Provider request failed"):
        await chat_completion(config, [{"role": "user", "content": "hello"}])


@pytest.mark.anyio
async def test_malformed_json_response_is_wrapped_as_provider_error(monkeypatch):
    config = ProviderConfig(
        preset=ProviderPreset.openai,
        base_url="https://api.openai.com/v1",
        api_key="secret",
        model="gpt-test",
        temperature=0.4,
    )

    class FakeResponse:
        status_code = 200
        text = "{not valid json}"

        def json(self):
            raise ValueError("malformed json")

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("backend.app.services.provider_adapter.httpx.AsyncClient", FakeClient)

    with pytest.raises(ProviderError, match="Provider response was not valid JSON"):
        await chat_completion(config, [{"role": "user", "content": "hello"}])
