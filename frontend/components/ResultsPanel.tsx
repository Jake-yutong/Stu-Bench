import type { EpisodeRunResult } from "../lib/types";
import { apiDownloadUrl } from "../lib/api";
import { ScoreGrid } from "./ScoreGrid";
import type { WorkbenchCopy } from "../lib/i18n";

export function ResultsPanel({
  result,
  runId,
  labels,
}: {
  result: EpisodeRunResult | null;
  runId: string | null;
  labels?: WorkbenchCopy;
}) {
  const scores = result?.judge_scores ?? null;
  const scoreLabels = labels
    ? [
        labels.scoreOverall,
        labels.scoreInitialState,
        labels.scoreMistake,
        labels.scoreUptake,
        labels.scoreKcTransition,
        labels.scoreTrajectory,
        labels.scoreOverCompetence,
      ]
    : undefined;

  return (
    <aside className="panel results-panel">
      <h2>{labels?.results ?? "Results"}</h2>
      <ScoreGrid scores={scores} labels={scoreLabels} />
      <div className="rationale">
        {String(scores?.judge_rationale ?? labels?.rationalePlaceholder ?? "Judge rationale will appear here after a run.")}
      </div>
      <div className="button-row">
        {runId ? (
          <>
            <a className="button-link" href={apiDownloadUrl(`/api/runs/${runId}/export.csv`)}>
              {labels?.exportCsv ?? "Export CSV"}
            </a>
            <a className="button-link" href={apiDownloadUrl(`/api/runs/${runId}/export.json`)}>
              {labels?.exportJson ?? "Export JSON"}
            </a>
          </>
        ) : (
          <>
            <button type="button" disabled>
              {labels?.exportCsv ?? "Export CSV"}
            </button>
            <button type="button" disabled>
              {labels?.exportJson ?? "Export JSON"}
            </button>
          </>
        )}
      </div>
    </aside>
  );
}
