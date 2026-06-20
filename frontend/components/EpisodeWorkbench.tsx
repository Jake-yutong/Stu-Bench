"use client";

import { useEffect, useState } from "react";

import { ApiConfigPanel, apiProviderPresets, studentProviderPresets } from "./ApiConfigPanel";
import { DialogueTimeline } from "./DialogueTimeline";
import { FormattedMathText } from "./FormattedMathText";
import { ResultsPanel } from "./ResultsPanel";
import { ThemeToggle } from "./ThemeToggle";
import { apiGet, apiPost } from "../lib/api";
import { formatMathText } from "../lib/formatMathText";
import { copy, type Language } from "../lib/i18n";
import type {
  EpisodeDetail,
  EpisodeRunResult,
  EpisodeSummary,
  ProviderConfig,
  ProviderTestResponse,
  RunPayload,
  RunStatus,
  TestMode,
} from "../lib/types";

const POLL_INTERVAL_MS = 1000;

const mockProvider: ProviderConfig = {
  preset: "mock",
  base_url: "mock://local",
  api_key: "mock",
  model: "mock-student",
  temperature: 0.7,
};

export function EpisodeWorkbench() {
  const [language, setLanguage] = useState<Language>("en");
  const t = copy[language];
  const [studentProvider, setStudentProvider] = useState<ProviderConfig>(mockProvider);
  const [judgeProvider, setJudgeProvider] = useState<ProviderConfig>({
    ...mockProvider,
    model: "mock-judge",
  });
  const [mode, setMode] = useState<TestMode>("context_engineered");
  const [episodes, setEpisodes] = useState<EpisodeSummary[]>([]);
  const [selectedEpisodeIds, setSelectedEpisodeIds] = useState<string[]>([]);
  const [activeEpisodeId, setActiveEpisodeId] = useState("");
  const [testCount, setTestCount] = useState(1);
  const [episode, setEpisode] = useState<EpisodeDetail | null>(null);
  const [run, setRun] = useState<RunPayload | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null);
  const [runError, setRunError] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<{
    student: string;
    judge: string;
  }>({ student: copy.en.studentNotTested, judge: copy.en.judgeNotTested });
  const [isTestingConnections, setIsTestingConnections] = useState(false);

  useEffect(() => {
    apiGet<{ episodes: EpisodeSummary[] }>("/api/episodes").then((payload) => {
      setEpisodes(payload.episodes);
      if (payload.episodes[0]) {
        setActiveEpisodeId(payload.episodes[0].episode_id);
        setTestCount(1);
      }
    });
  }, []);

  useEffect(() => {
    if (!activeEpisodeId) return;
    apiGet<EpisodeDetail>(`/api/episodes/${activeEpisodeId}`).then(setEpisode);
  }, [activeEpisodeId]);

  function changeLanguage(nextLanguage: Language) {
    setLanguage(nextLanguage);
    setConnectionStatus({
      student: copy[nextLanguage].studentNotTested,
      judge: copy[nextLanguage].judgeNotTested,
    });
  }

  function toggleEpisode(episodeId: string) {
    setActiveEpisodeId(episodeId);
    setSelectedEpisodeIds((current) =>
      current.includes(episodeId)
        ? current.filter((item) => item !== episodeId)
        : [...current, episodeId],
    );
  }

  function changeTestCount(value: string) {
    const parsed = Number(value);
    const max = Math.max(episodes.length, 1);
    const nextCount = Number.isFinite(parsed) ? Math.min(Math.max(parsed, 1), max) : 1;
    setTestCount(nextCount);
    if (selectedEpisodeIds.length === 0 && episodes[0]) {
      setActiveEpisodeId(episodes[0].episode_id);
    }
  }

  function runEpisodeIds() {
    if (selectedEpisodeIds.length > 0) {
      return episodes
        .filter((item) => selectedEpisodeIds.includes(item.episode_id))
        .map((item) => item.episode_id);
    }
    return episodes.slice(0, Math.min(testCount, episodes.length)).map((item) => item.episode_id);
  }

  function updateRunFromStatus(status: RunStatus) {
    setRunStatus(status);
    if (status.results) {
      setRun({ run_id: status.run_id, results: status.results });
    }

    const latestResult = status.results?.[status.results.length - 1] ?? null;
    const displayEpisodeId = status.current_episode_id ?? latestResult?.episode_id;
    if (displayEpisodeId) {
      setActiveEpisodeId(displayEpisodeId);
    }
  }

  async function pollRun(nextRunId: string) {
    const status = await apiGet<RunStatus>(`/api/runs/${nextRunId}/events`);
    updateRunFromStatus(status);

    if (status.status === "failed") {
      setRunError(status.error_message ?? "Run failed.");
      setIsRunning(false);
      return;
    }

    if (status.status === "completed") {
      const payload = await apiGet<RunPayload>(`/api/runs/${nextRunId}`);
      setRun(payload);
      const latestResult = payload.results[payload.results.length - 1];
      if (latestResult) {
        setActiveEpisodeId(latestResult.episode_id);
      }
      setIsRunning(false);
      return;
    }

    window.setTimeout(() => {
      void pollRun(nextRunId);
    }, POLL_INTERVAL_MS);
  }

  async function runSelected() {
    const episodeIds = runEpisodeIds();
    if (episodeIds.length === 0) return;
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
      updateRunFromStatus(status);
      void pollRun(status.run_id);
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "Run request failed.");
      setIsRunning(false);
    }
  }

  async function testProvider(label: string, provider: ProviderConfig) {
    try {
      const result = await apiPost<ProviderTestResponse>("/api/providers/test", provider);
      return `${label}: ${result.sample || (result.ok ? t.connectionOk : t.failed)}`;
    } catch (error) {
      return `${label}: ${error instanceof Error ? error.message : t.failed}`;
    }
  }

  async function testConnections() {
    setIsTestingConnections(true);
    setConnectionStatus({
      student: t.studentTesting,
      judge: t.judgeTesting,
    });
    const [student, judge] = await Promise.all([
      testProvider(t.studentApi, studentProvider),
      testProvider(t.judgeApi, judgeProvider),
    ]);
    setConnectionStatus({ student, judge });
    setIsTestingConnections(false);
  }

  const runStatusText = runStatus
    ? `${runStatus.status}: ${runStatus.completed}/${runStatus.total}`
    : t.idleStatus;
  const latestResult = run?.results?.[run.results.length - 1] ?? null;
  const activeResult: EpisodeRunResult | null =
    run?.results?.find((result) => result.episode_id === activeEpisodeId) ?? latestResult;

  return (
    <main className="workbench">
      <header className="topbar">
        <div>
          <h1>{t.appTitle}</h1>
          <p>{t.appSubtitle}</p>
        </div>
        <div className="top-actions">
          <label className="compact-label">
            {t.language}
            <select
              aria-label="Language"
              value={language}
              onChange={(event) => changeLanguage(event.target.value as Language)}
            >
              <option value="en">{t.english}</option>
              <option value="zh">{t.chinese}</option>
            </select>
          </label>
          <ThemeToggle label={t.toggleTheme} />
        </div>
      </header>
      <section className="columns">
        <aside className="panel setup-panel">
          <ApiConfigPanel
            title={t.studentApi}
            providerLabel={t.studentProvider}
            provider={studentProvider}
            onChange={setStudentProvider}
            presets={studentProviderPresets}
            labels={{
              baseUrl: t.baseUrl,
              model: t.model,
              apiKey: t.apiKey,
              temperature: t.temperature,
            }}
          />
          <ApiConfigPanel
            title={t.judgeApi}
            providerLabel={t.judgeProvider}
            provider={judgeProvider}
            onChange={setJudgeProvider}
            presets={apiProviderPresets}
            labels={{
              baseUrl: t.baseUrl,
              model: t.model,
              apiKey: t.apiKey,
              temperature: t.temperature,
            }}
          />
          <label>
            {t.testingMode}
            <select
              aria-label="Testing mode"
              value={mode}
              onChange={(event) => setMode(event.target.value as TestMode)}
            >
              <option value="roleplay">{t.roleplay}</option>
              <option value="profile">{t.profile}</option>
              <option value="context_engineered">{t.contextEngineered}</option>
            </select>
          </label>
          <label>
            {t.testCount}
            <input
              aria-label="Test count"
              type="number"
              min="1"
              max={Math.max(episodes.length, 1)}
              value={testCount}
              onChange={(event) => changeTestCount(event.target.value)}
            />
          </label>
          <div className="field-label">{t.episodeSelection}</div>
          <div className="episode-picker" role="group" aria-label={t.episodeSelection}>
            {episodes.map((item) => (
              <label
                className={item.episode_id === activeEpisodeId ? "checkbox-row active" : "checkbox-row"}
                key={item.episode_id}
              >
                <input
                  aria-label={item.episode_id}
                  type="checkbox"
                  checked={selectedEpisodeIds.includes(item.episode_id)}
                  onChange={() => toggleEpisode(item.episode_id)}
                />
                <span>
                  <strong>{item.episode_id}</strong>
                  <small>{formatMathText(item.problem_preview).replace(/\n/g, " ")}</small>
                </span>
              </label>
            ))}
          </div>
          <label className="sr-only">
            {t.episode}
            <select value={activeEpisodeId} onChange={(event) => setActiveEpisodeId(event.target.value)}>
              {episodes.map((item) => (
                <option key={item.episode_id} value={item.episode_id}>
                  {item.episode_id}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={testConnections} disabled={isTestingConnections}>
            {isTestingConnections ? t.testing : t.testConnections}
          </button>
          <div className="status-stack" aria-live="polite">
            <div>{connectionStatus.student}</div>
            <div>{connectionStatus.judge}</div>
          </div>
          <button type="button" onClick={runSelected} disabled={isRunning}>
            {isRunning ? t.running : t.runSelected}
          </button>
          <div className="status-stack" aria-live="polite">
            <div>{runStatusText}</div>
            {runStatus?.current_episode_id ? <div>{runStatus.current_episode_id}</div> : null}
            {runError ? <div className="error-text">{runError}</div> : null}
          </div>
        </aside>
        <section className="panel episode-panel">
          <h2>{t.episode}</h2>
          <div className="question-box">
            {episode ? (
              <>
                <strong>
                  <FormattedMathText text={episode.problem.text} />
                </strong>
                <ul>
                  {episode.problem.answer_options.map((option) => (
                    <li key={option.label}>
                      <FormattedMathText text={`${option.label}. ${option.text}`} />
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              t.loadingEpisode
            )}
          </div>
          <div className="context-grid">
            <div>
              {episode ? (
                <pre>{JSON.stringify(episode.lcs.scs, null, 2)}</pre>
              ) : (
                t.scsSummary
              )}
            </div>
            <div>
              {episode
                ? episode.lcs.scaffold_sequence.map((turn) => turn.message).join("\n")
                : t.scaffoldSequence}
            </div>
          </div>
          <DialogueTimeline
            turns={activeResult?.generated_trajectory ?? []}
            labels={{
              ariaLabel: t.dialogueTimeline,
              emptyTutor: t.emptyTutor,
              emptyStudent: t.emptyStudent,
              tutorPrefix: t.tutorPrefix,
              studentPrefix: t.studentPrefix,
            }}
          />
        </section>
        <ResultsPanel result={activeResult} runId={runId} labels={t} />
      </section>
    </main>
  );
}
