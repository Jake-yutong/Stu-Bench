"use client";

import { useState } from "react";

import { ApiConfigPanel } from "./ApiConfigPanel";
import { DialogueTimeline } from "./DialogueTimeline";
import { ResultsPanel } from "./ResultsPanel";
import { ThemeToggle } from "./ThemeToggle";
import type { ProviderConfig, TestMode } from "../lib/types";

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
          <button type="button">Test connections</button>
          <button type="button">Run current</button>
          <button type="button">Run selected</button>
        </aside>
        <section className="panel episode-panel">
          <h2>Episode</h2>
          <div className="question-box">Question and answer options will load here.</div>
          <div className="context-grid">
            <div>SCS summary</div>
            <div>Scaffold sequence</div>
          </div>
          <DialogueTimeline />
        </section>
        <ResultsPanel />
      </section>
    </main>
  );
}
