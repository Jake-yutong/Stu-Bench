export type ProviderPreset = "openai" | "deepseek" | "qwen" | "custom" | "mock";
export type TestMode = "roleplay" | "profile" | "context_engineered";

export interface ProviderConfig {
  preset: ProviderPreset;
  base_url: string;
  api_key: string;
  model: string;
  temperature: number;
}
