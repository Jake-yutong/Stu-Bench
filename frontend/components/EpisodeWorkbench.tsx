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
  RunPayload,
  TestMode,
} from "../lib/types";

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

  async function runSelected() {
    const episodeIds = selectedEpisodeId
      ? [selectedEpisodeId]
      : episodes.map((item) => item.episode_id);
    const payload = await apiPost<RunPayload>("/api/runs", {
      mode,
      student_provider: studentProvider,
      judge_provider: judgeProvider,
      episode_ids: episodeIds,
    });
    setRun(payload);
  }

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
          <button type="button">Test connections</button>
          <button type="button" onClick={runSelected}>
            Run selected
          </button>
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
          <DialogueTimeline turns={run?.results[0]?.generated_trajectory ?? []} />
        </section>
        <ResultsPanel run={run} />
      </section>
    </main>
  );
}
