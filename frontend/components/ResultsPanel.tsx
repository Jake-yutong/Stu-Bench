import { useState } from "react";

import type { EpisodeRunResult } from "../lib/types";
import { apiDownloadUrl, apiGet } from "../lib/api";
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
  const [jsonExport, setJsonExport] = useState("");
  const [jsonError, setJsonError] = useState("");
  const [isJsonModalOpen, setIsJsonModalOpen] = useState(false);
  const [isJsonLoading, setIsJsonLoading] = useState(false);
  const scoreLabels = labels
    ? [
        labels.scoreOverall,
        labels.scoreInitialState,
        labels.scoreMistake,
        labels.scoreUptake,
        labels.scoreKcTransition,
        labels.scoreOverCompetence,
      ]
    : undefined;

  async function openJsonExport() {
    if (!runId) return;
    setIsJsonModalOpen(true);
    setIsJsonLoading(true);
    setJsonError("");
    try {
      const payload = await apiGet<unknown>(`/api/runs/${runId}/export.json`);
      setJsonExport(JSON.stringify(payload, null, 2));
    } catch (error) {
      setJsonExport("");
      setJsonError(error instanceof Error ? error.message : labels?.jsonExportError ?? "Could not load JSON export.");
    } finally {
      setIsJsonLoading(false);
    }
  }

  function closeJsonExport() {
    setIsJsonModalOpen(false);
  }

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
            <button type="button" onClick={openJsonExport}>
              {labels?.exportJson ?? "Export JSON"}
            </button>
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
      {isJsonModalOpen ? (
        <div className="modal-backdrop">
          <div className="modal" role="dialog" aria-modal="true" aria-label={labels?.jsonExportTitle ?? "Export JSON"}>
            <div className="modal-header">
              <h3>{labels?.jsonExportTitle ?? "Export JSON"}</h3>
              <button type="button" onClick={closeJsonExport}>
                {labels?.close ?? "Close"}
              </button>
            </div>
            <pre className="json-export">
              {isJsonLoading
                ? labels?.jsonExportLoading ?? "Loading JSON export..."
                : jsonError || jsonExport}
            </pre>
          </div>
        </div>
      ) : null}
    </aside>
  );
}
