import type { ProviderConfig } from "../lib/types";

interface Props {
  title: string;
  provider: ProviderConfig;
  onChange: (provider: ProviderConfig) => void;
  providerLabel: string;
  presets?: readonly ProviderConfig["preset"][];
  labels: {
    baseUrl: string;
    model: string;
    apiKey: string;
    temperature: string;
  };
}

export const apiProviderPresets = ["openai", "deepseek", "qwen", "custom", "mock"] as const;
export const studentProviderPresets = [
  "openai",
  "deepseek",
  "qwen",
  "custom",
  "local-vllm-sft",
  "local-vllm-dpo",
  "mock",
] as const;

const presetBaseUrls: Record<ProviderConfig["preset"], string> = {
  openai: "https://api.openai.com/v1",
  deepseek: "https://api.deepseek.com",
  qwen: "https://dashscope.aliyuncs.com/compatible-mode/v1",
  custom: "",
  "local-vllm-sft": "http://127.0.0.1:8010/v1",
  "local-vllm-dpo": "http://127.0.0.1:8010/v1",
  mock: "mock://local",
};

const presetDefaultModels: Record<ProviderConfig["preset"], string> = {
  openai: "",
  deepseek: "",
  qwen: "",
  custom: "",
  "local-vllm-sft": "eedi-stud-sft-8b",
  "local-vllm-dpo": "eedi-stud-dpo-8b",
  mock: "",
};

export function ApiConfigPanel({
  title,
  provider,
  onChange,
  providerLabel,
  presets = apiProviderPresets,
  labels,
}: Props) {
  function changePreset(preset: ProviderConfig["preset"]) {
    const defaultModel = presetDefaultModels[preset];
    onChange({
      ...provider,
      preset,
      base_url: preset === "custom" ? provider.base_url : presetBaseUrls[preset],
      model: defaultModel || provider.model,
    });
  }

  return (
    <section className="panel-block" aria-label={title}>
      <h2>{title}</h2>
      <label>
        {providerLabel}
        <select
          aria-label={providerLabel}
          value={provider.preset}
          onChange={(event) => changePreset(event.target.value as ProviderConfig["preset"])}
        >
          {presets.map((preset) => (
            <option key={preset} value={preset}>
              {preset}
            </option>
          ))}
        </select>
      </label>
      <label>
        {labels.baseUrl}
        <input
          value={provider.base_url}
          onChange={(event) => onChange({ ...provider, base_url: event.target.value })}
        />
      </label>
      <label>
        {labels.model}
        <input
          value={provider.model}
          onChange={(event) => onChange({ ...provider, model: event.target.value })}
        />
      </label>
      <label>
        {labels.apiKey}
        <input
          type="password"
          value={provider.api_key}
          onChange={(event) => onChange({ ...provider, api_key: event.target.value })}
        />
      </label>
      <label>
        {labels.temperature}
        <input
          type="number"
          min="0"
          max="2"
          step="0.1"
          value={provider.temperature}
          onChange={(event) =>
            onChange({ ...provider, temperature: Number(event.target.value) })
          }
        />
      </label>
    </section>
  );
}
