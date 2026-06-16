const fields = [
  "lrs",
  "isf",
  "ma",
  "su",
  "ktc",
  "occ",
] as const;

function formatScore(value: unknown) {
  if (typeof value !== "number") {
    return "--";
  }
  return value.toFixed(3);
}

export function ScoreGrid({
  scores,
  labels = [
    "LRS",
    "ISF",
    "MA",
    "SU",
    "KTC",
    "OCC",
  ],
}: {
  scores: Record<string, unknown> | null;
  labels?: string[];
}) {
  return (
    <div className="score-grid">
      {fields.map((field, index) => (
        <div className="score-card" key={field}>
          <span>{labels[index]}</span>
          <strong>{scores ? formatScore(scores[field]) : "--"}</strong>
        </div>
      ))}
    </div>
  );
}
