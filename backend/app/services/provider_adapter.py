import httpx

from backend.app.data.schemas import ProviderConfig, ProviderPreset


class ProviderError(RuntimeError):
    pass


def provider_base_url(preset: ProviderPreset) -> str:
    defaults = {
        ProviderPreset.openai: "https://api.openai.com/v1",
        ProviderPreset.deepseek: "https://api.deepseek.com",
        ProviderPreset.qwen: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ProviderPreset.local_vllm_sft: "http://127.0.0.1:8010/v1",
        ProviderPreset.local_vllm_dpo: "http://127.0.0.1:8010/v1",
        ProviderPreset.mock: "mock://local",
        ProviderPreset.custom: "",
    }
    return defaults[preset]


def provider_default_model(preset: ProviderPreset) -> str:
    defaults = {
        ProviderPreset.openai: "",
        ProviderPreset.deepseek: "",
        ProviderPreset.qwen: "",
        ProviderPreset.local_vllm_sft: "eedi-stud-sft-8b",
        ProviderPreset.local_vllm_dpo: "eedi-stud-dpo-8b",
        ProviderPreset.mock: "mock-student",
        ProviderPreset.custom: "",
    }
    return defaults[preset]


async def chat_completion(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    max_tokens: int = 600,
) -> str:
    if config.preset == ProviderPreset.mock:
        return _mock_response(config, messages)

    url = config.base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}
    payload = {
        "model": config.model or provider_default_model(config.preset),
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": max_tokens,
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        reason = str(exc) or exc.__class__.__name__
        raise ProviderError(f"Provider request failed: {reason}") from exc
    if response.status_code >= 400:
        raise ProviderError(f"Provider returned HTTP {response.status_code}")
    try:
        data = response.json()
    except ValueError as exc:
        raise ProviderError(f"Provider response was not valid JSON: {exc}") from exc
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("Provider response did not contain choices[0].message.content") from exc
    if not isinstance(content, str) or not content.strip():
        raise ProviderError("Provider response did not contain choices[0].message.content")
    return content.strip()


def _mock_response(config: ProviderConfig, messages: list[dict[str, str]]) -> str:
    joined = "\n".join(message["content"] for message in messages)
    if "JSON" in joined or "judge" in config.model.lower():
        return (
            '{"lrs": 0.78, "isf": 0.76, "ma": 0.74, "su": 0.80, '
            '"ktc": 0.72, "occ": 0.83, '
            '"judge_rationale": "Mock judge: plausible gradual uptake.", '
            '"failure_flags": [], "formula_metrics": {"kts": null, "uptake": null, '
            '"over_improve": null, "status": "judge_estimated"}}'
        )
    return "I think I understand part of it, but I need to check the next digit."
