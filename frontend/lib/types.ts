export type ProviderPreset = "openai" | "deepseek" | "qwen" | "custom" | "mock";
export type TestMode = "roleplay" | "profile" | "context_engineered";

export interface ProviderConfig {
  preset: ProviderPreset;
  base_url: string;
  api_key: string;
  model: string;
  temperature: number;
}

export interface ProviderTestResponse {
  ok: boolean;
  sample?: string;
  detail?: string;
}

export type RunStatusValue = "queued" | "running" | "completed" | "failed";

export interface RunStatus {
  run_id: string;
  status: RunStatusValue;
  total: number;
  completed: number;
  current_episode_id?: string | null;
  error_message?: string | null;
}

export interface EpisodeSummary {
  episode_id: string;
  question_id: number;
  intervention_id: number;
  problem_preview: string;
  scaffold_turns: number;
}

export interface EpisodeDetail {
  episode_id: string;
  problem: {
    text: string;
    answer_options: Array<{ label: string; text: string }>;
  };
  lcs: {
    scs: Record<string, unknown>;
    scaffold_sequence: Array<{ message: string }>;
  };
}

export interface RunPayload {
  run_id: string;
  results: Array<{
    episode_id: string;
    status: "succeeded" | "failed";
    generated_trajectory: Array<{
      turn_index: number;
      tutor_message: string;
      student_response: string;
    }>;
    judge_scores?: Record<string, unknown>;
    error_message?: string;
  }>;
}
