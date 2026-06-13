import type { RunPayload } from "../lib/types";
import { apiDownloadUrl } from "../lib/api";
import { ScoreGrid } from "./ScoreGrid";

export function ResultsPanel({ run, runId }: { run: RunPayload | null; runId: string | null }) {
  const scores = run?.results[0]?.judge_scores ?? null;

  return (
    <aside className="panel results-panel">
      <h2>Results</h2>
      <ScoreGrid scores={scores} />
      <div className="rationale">
        {String(scores?.judge_rationale ?? "Judge rationale will appear here after a run.")}
      </div>
      <div className="button-row">
        {runId ? (
          <>
            <a className="button-link" href={apiDownloadUrl(`/api/runs/${runId}/export.csv`)}>
              Export CSV
            </a>
            <a className="button-link" href={apiDownloadUrl(`/api/runs/${runId}/export.json`)}>
              Export JSON
            </a>
          </>
        ) : (
          <>
            <button type="button" disabled>
              Export CSV
            </button>
            <button type="button" disabled>
              Export JSON
            </button>
          </>
        )}
      </div>
    </aside>
  );
}
