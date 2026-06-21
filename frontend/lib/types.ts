export type ProviderPreset =
  | "openai"
  | "deepseek"
  | "qwen"
  | "custom"
  | "local-vllm-sft"
  | "local-vllm-dpo"
  | "mock";
export type TestMode = "roleplay" | "profile" | "context_engineered";
export type MetricStatus = "computed" | "judge_estimated" | "pending_annotation";

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
  results?: EpisodeRunResult[];
  error_message?: string | null;
}

export interface EpisodeSummary {
  episode_id: string;
  question_id: number;
  intervention_id: number;
  source_split: "test" | "val" | "train";
  problem_preview: string;
  scaffold_turns: number;
}

export interface MetricStatusInfo {
  metric_id: string;
  display_name: string;
  current_status: MetricStatus;
  computed_when: string;
}

export interface DatasetSummary {
  official_split: string;
  episode_count: number;
  unique_questions: number;
  subject_distribution: Record<string, number>;
  length_distribution: Record<string, number>;
  annotation_schema: {
    title: string;
    annotation_version: string;
    gold_provenance_values: string[];
  };
  metric_statuses: MetricStatusInfo[];
}

export interface EpisodeDetail {
  episode_id: string;
  source_split: "test" | "val" | "train";
  problem: {
    text: string;
    answer_options: Array<{ label: string; text: string }>;
  };
  lcs: {
    scs: Record<string, unknown>;
    scaffold_sequence: Array<{ message: string }>;
  };
}

export interface EpisodeRunResult {
  episode_id: string;
  status: "succeeded" | "failed";
  generated_trajectory: Array<{
    turn_index: number;
    tutor_message: string;
    student_response: string;
  }>;
  judge_scores?: Record<string, unknown>;
  error_message?: string;
}

export interface RunPayload {
  run_id: string;
  results: EpisodeRunResult[];
}
