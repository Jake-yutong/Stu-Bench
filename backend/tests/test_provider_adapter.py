import pytest
import httpx

from backend.app.data.schemas import ProviderConfig, ProviderPreset
from backend.app.services.provider_adapter import (
    ProviderError,
    chat_completion,
    provider_base_url,
    provider_default_model,
)


def test_provider_presets_resolve_base_urls():
    assert provider_base_url(ProviderPreset.openai) == "https://api.openai.com/v1"
    assert provider_base_url(ProviderPreset.deepseek) == "https://api.deepseek.com"
    assert provider_base_url(ProviderPreset.qwen) == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert provider_base_url(ProviderPreset.local_vllm_sft) == "http://127.0.0.1:8010/v1"
    assert provider_base_url(ProviderPreset.local_vllm_dpo) == "http://127.0.0.1:8010/v1"


def test_local_vllm_presets_resolve_adapter_model_names():
    assert provider_default_model(ProviderPreset.local_vllm_sft) == "eedi-stud-sft-8b"
    assert provider_default_model(ProviderPreset.local_vllm_dpo) == "eedi-stud-dpo-8b"


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
async def test_local_vllm_provider_uses_openai_compatible_chat_endpoint(monkeypatch):
    config = ProviderConfig(
        preset=ProviderPreset.local_vllm_dpo,
        base_url="http://127.0.0.1:8010/v1",
        api_key="local",
        model="eedi-stud-dpo-8b",
        temperature=0.6,
    )
    captured: dict[str, object] = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "local dpo student reply"}}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            captured["timeout"] = kwargs.get("timeout")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers, json):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr("backend.app.services.provider_adapter.httpx.AsyncClient", FakeClient)

    text = await chat_completion(config, [{"role": "user", "content": "Tutor message"}])

    assert text == "local dpo student reply"
    assert captured["url"] == "http://127.0.0.1:8010/v1/chat/completions"
    assert captured["json"]["model"] == "eedi-stud-dpo-8b"
    assert captured["json"]["temperature"] == 0.6


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
async def test_non_2xx_response_does_not_expose_body_text(monkeypatch):
    config = ProviderConfig(
        preset=ProviderPreset.openai,
        base_url="https://api.openai.com/v1",
        api_key="secret",
        model="gpt-test",
        temperature=0.4,
    )

    class FakeResponse:
        status_code = 403
        text = "sentinel-secret-body-token"

        def json(self):
            return {}

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

    with pytest.raises(ProviderError) as exc_info:
        await chat_completion(config, [{"role": "user", "content": "hello"}])

    message = str(exc_info.value)
    assert "Provider returned HTTP 403" in message
    assert "sentinel-secret-body-token" not in message


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


@pytest.mark.anyio
async def test_null_content_is_wrapped_as_provider_error(monkeypatch):
    config = ProviderConfig(
        preset=ProviderPreset.openai,
        base_url="https://api.openai.com/v1",
        api_key="secret",
        model="gpt-test",
        temperature=0.4,
    )

    class FakeResponse:
        status_code = 200
        text = '{"choices":[{"message":{"content":null}}]}'

        def json(self):
            return {"choices": [{"message": {"content": None}}]}

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

    with pytest.raises(ProviderError, match="Provider response did not contain choices\\[0\\]\\.message\\.content"):
        await chat_completion(config, [{"role": "user", "content": "hello"}])


@pytest.mark.anyio
async def test_blank_content_is_wrapped_as_provider_error(monkeypatch):
    config = ProviderConfig(
        preset=ProviderPreset.openai,
        base_url="https://api.openai.com/v1",
        api_key="secret",
        model="gpt-test",
        temperature=0.4,
    )

    class FakeResponse:
        status_code = 200
        text = '{"choices":[{"message":{"content":"   "}}]}'

        def json(self):
            return {"choices": [{"message": {"content": "   "}}]}

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

    with pytest.raises(ProviderError, match="Provider response did not contain choices\\[0\\]\\.message\\.content"):
        await chat_completion(config, [{"role": "user", "content": "hello"}])
