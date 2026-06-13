import { ScoreGrid } from "./ScoreGrid";

export function ResultsPanel() {
  return (
    <aside className="panel results-panel">
      <h2>Results</h2>
      <ScoreGrid />
      <div className="rationale">Judge rationale will appear here after a run.</div>
      <div className="button-row">
        <button type="button">Export CSV</button>
        <button type="button">Export JSON</button>
      </div>
    </aside>
  );
}
