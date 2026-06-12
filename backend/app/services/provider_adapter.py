import httpx

from backend.app.data.schemas import ProviderConfig, ProviderPreset


class ProviderError(RuntimeError):
    pass


def provider_base_url(preset: ProviderPreset) -> str:
    defaults = {
        ProviderPreset.openai: "https://api.openai.com/v1",
        ProviderPreset.deepseek: "https://api.deepseek.com",
        ProviderPreset.qwen: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ProviderPreset.mock: "mock://local",
        ProviderPreset.custom: "",
    }
    return defaults[preset]


async def chat_completion(config: ProviderConfig, messages: list[dict[str, str]]) -> str:
    if config.preset == ProviderPreset.mock:
        return _mock_response(config, messages)

    url = config.base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": 600,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=headers, json=payload)
    if response.status_code >= 400:
        raise ProviderError(f"Provider returned {response.status_code}: {response.text[:500]}")
    data = response.json()
    try:
        return str(data["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("Provider response did not contain choices[0].message.content") from exc


def _mock_response(config: ProviderConfig, messages: list[dict[str, str]]) -> str:
    joined = "\n".join(message["content"] for message in messages)
    if "JSON" in joined or "judge" in config.model.lower():
        return (
            '{"overall_realism": 78, "initial_state_fidelity": 76, '
            '"mistake_authenticity": 74, "scaffolding_uptake": 80, '
            '"kc_transition_consistency": 72, "learning_trajectory_plausibility": 79, '
            '"over_competence_control": 83, "judge_rationale": "Mock judge: plausible gradual uptake.", '
            '"failure_flags": [], "formula_metrics": {"kts": null, "uptake": null, '
            '"over_improve": null, "status": "judge_estimated"}}'
        )
    return "I think I understand part of it, but I need to check the next digit."
