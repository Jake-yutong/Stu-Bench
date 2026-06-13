const labels = [
  "Overall",
  "Initial State",
  "Mistake Auth.",
  "Uptake",
  "KC Transition",
  "Trajectory",
  "Over-Competence Control",
];

export function ScoreGrid() {
  return (
    <div className="score-grid">
      {labels.map((label) => (
        <div className="score-card" key={label}>
          <span>{label}</span>
          <strong>--</strong>
        </div>
      ))}
    </div>
  );
}
