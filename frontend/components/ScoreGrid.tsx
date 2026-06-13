const fields = [
  "overall_realism",
  "initial_state_fidelity",
  "mistake_authenticity",
  "scaffolding_uptake",
  "kc_transition_consistency",
  "learning_trajectory_plausibility",
  "over_competence_control",
] as const;

export function ScoreGrid({
  scores,
  labels = [
    "Overall",
    "Initial State",
    "Mistake Auth.",
    "Uptake",
    "KC Transition",
    "Trajectory",
    "Over-Competence Control",
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
          <strong>{scores ? String(scores[field] ?? "--") : "--"}</strong>
        </div>
      ))}
    </div>
  );
}
