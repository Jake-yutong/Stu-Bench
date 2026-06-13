import type { RunPayload } from "../lib/types";
import { ScoreGrid } from "./ScoreGrid";

export function ResultsPanel({ run }: { run: RunPayload | null }) {
  const scores = run?.results[0]?.judge_scores ?? null;

  return (
    <aside className="panel results-panel">
      <h2>Results</h2>
      <ScoreGrid scores={scores} />
      <div className="rationale">
        {String(scores?.judge_rationale ?? "Judge rationale will appear here after a run.")}
      </div>
      <div className="button-row">
        <button type="button">Export CSV</button>
        <button type="button">Export JSON</button>
      </div>
    </aside>
  );
}
