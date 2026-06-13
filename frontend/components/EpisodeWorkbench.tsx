"use client";

import { useEffect, useState } from "react";

import { ApiConfigPanel } from "./ApiConfigPanel";
import { DialogueTimeline } from "./DialogueTimeline";
import { ResultsPanel } from "./ResultsPanel";
import { ThemeToggle } from "./ThemeToggle";
import { apiGet, apiPost } from "../lib/api";
import type {
  EpisodeDetail,
  EpisodeSummary,
  ProviderConfig,
  ProviderTestResponse,
  RunPayload,
  RunStatus,
  TestMode,
} from "../lib/types";

const POLL_INTERVAL_MS = 250;

const mockProvider: ProviderConfig = {
  preset: "mock",
  base_url: "mock://local",
  api_key: "mock",
  model: "mock-student",
  temperature: 0.7,
};

export function EpisodeWorkbench() {
  const [studentProvider, setStudentProvider] = useState<ProviderConfig>(mockProvider);
  const [judgeProvider, setJudgeProvider] = useState<ProviderConfig>({
    ...mockProvider,
    model: "mock-judge",
  });
  const [mode, setMode] = useState<TestMode>("context_engineered");
  const [episodes, setEpisodes] = useState<EpisodeSummary[]>([]);
  const [selectedEpisodeId, setSelectedEpisodeId] = useState("");
  const [episode, setEpisode] = useState<EpisodeDetail | null>(null);
  const [run, setRun] = useState<RunPayload | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null);
  const [runError, setRunError] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<{
    student: string;
    judge: string;
  }>({ student: "Student API: not tested", judge: "Judge API: not tested" });
  const [isTestingConnections, setIsTestingConnections] = useState(false);

  useEffect(() => {
    apiGet<{ episodes: EpisodeSummary[] }>("/api/episodes").then((payload) => {
      setEpisodes(payload.episodes);
      if (payload.episodes[0]) {
        setSelectedEpisodeId(payload.episodes[0].episode_id);
      }
    });
  }, []);

  useEffect(() => {
    if (!selectedEpisodeId) return;
    apiGet<EpisodeDetail>(`/api/episodes/${selectedEpisodeId}`).then(setEpisode);
  }, [selectedEpisodeId]);

  async function pollRun(nextRunId: string) {
    const status = await apiGet<RunStatus>(`/api/runs/${nextRunId}/events`);
    setRunStatus(status);

    if (status.status === "failed") {
      setRunError(status.error_message ?? "Run failed.");
      setIsRunning(false);
      return;
    }

    if (status.status === "completed") {
      const payload = await apiGet<RunPayload>(`/api/runs/${nextRunId}`);
      setRun(payload);
      setIsRunning(false);
      return;
    }

    window.setTimeout(() => {
      void pollRun(nextRunId);
    }, POLL_INTERVAL_MS);
  }

  async function runSelected() {
    const episodeIds = selectedEpisodeId
      ? [selectedEpisodeId]
      : episodes.map((item) => item.episode_id);
    try {
      setRun(null);
      setRunId(null);
      setRunStatus(null);
      setRunError("");
      setIsRunning(true);
      const status = await apiPost<RunStatus>("/api/runs", {
        mode,
        student_provider: studentProvider,
        judge_provider: judgeProvider,
        episode_ids: episodeIds,
      });
      setRunId(status.run_id);
      setRunStatus(status);
      void pollRun(status.run_id);
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "Run request failed.");
      setIsRunning(false);
    }
  }

  async function testProvider(label: "Student API" | "Judge API", provider: ProviderConfig) {
    try {
      const result = await apiPost<ProviderTestResponse>("/api/providers/test", provider);
      return `${label}: ${result.sample || (result.ok ? "connection ok" : "failed")}`;
    } catch (error) {
      return `${label}: ${error instanceof Error ? error.message : "connection failed"}`;
    }
  }

  async function testConnections() {
    setIsTestingConnections(true);
    setConnectionStatus({
      student: "Student API: testing...",
      judge: "Judge API: testing...",
    });
    const [student, judge] = await Promise.all([
      testProvider("Student API", studentProvider),
      testProvider("Judge API", judgeProvider),
    ]);
    setConnectionStatus({ student, judge });
    setIsTestingConnections(false);
  }

  const runStatusText = runStatus
    ? `${runStatus.status}: ${runStatus.completed}/${runStatus.total}`
    : "idle: 0/0";

  return (
    <main className="workbench">
      <header className="topbar">
        <div>
          <h1>Stu-Bench Demo</h1>
          <p>Local-first benchmark workbench for simulated student realism.</p>
        </div>
        <ThemeToggle />
      </header>
      <section className="columns">
        <aside className="panel setup-panel">
          <ApiConfigPanel
            title="Student API"
            providerLabel="Student provider"
            provider={studentProvider}
            onChange={setStudentProvider}
          />
          <ApiConfigPanel
            title="Judge API"
            providerLabel="Judge provider"
            provider={judgeProvider}
            onChange={setJudgeProvider}
          />
          <label>
            Testing mode
            <select
              aria-label="Testing mode"
              value={mode}
              onChange={(event) => setMode(event.target.value as TestMode)}
            >
              <option value="roleplay">Roleplay Prompt</option>
              <option value="profile">Profile Prompt</option>
              <option value="context_engineered">Context-Engineered SCS</option>
            </select>
          </label>
          <label>
            Episode
            <select
              value={selectedEpisodeId}
              onChange={(event) => setSelectedEpisodeId(event.target.value)}
            >
              {episodes.map((item) => (
                <option key={item.episode_id} value={item.episode_id}>
                  {item.episode_id}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={testConnections} disabled={isTestingConnections}>
            {isTestingConnections ? "Testing..." : "Test connections"}
          </button>
          <div className="status-stack" aria-live="polite">
            <div>{connectionStatus.student}</div>
            <div>{connectionStatus.judge}</div>
          </div>
          <button type="button" onClick={runSelected} disabled={isRunning}>
            {isRunning ? "Running..." : "Run selected"}
          </button>
          <div className="status-stack" aria-live="polite">
            <div>{runStatusText}</div>
            {runStatus?.current_episode_id ? <div>{runStatus.current_episode_id}</div> : null}
            {runError ? <div className="error-text">{runError}</div> : null}
          </div>
        </aside>
        <section className="panel episode-panel">
          <h2>Episode</h2>
          <div className="question-box">
            {episode ? (
              <>
                <strong>{episode.problem.text}</strong>
                <ul>
                  {episode.problem.answer_options.map((option) => (
                    <li key={option.label}>
                      {option.label}. {option.text}
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              "Loading episode..."
            )}
          </div>
          <div className="context-grid">
            <div>
              {episode ? (
                <pre>{JSON.stringify(episode.lcs.scs, null, 2)}</pre>
              ) : (
                "SCS summary"
              )}
            </div>
            <div>
              {episode
                ? episode.lcs.scaffold_sequence.map((turn) => turn.message).join("\n")
                : "Scaffold sequence"}
            </div>
          </div>
          <DialogueTimeline turns={run?.results?.[0]?.generated_trajectory ?? []} />
        </section>
        <ResultsPanel run={run} runId={runId} />
      </section>
    </main>
  );
}
