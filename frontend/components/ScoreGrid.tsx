const fields = [
  ["overall_realism", "Overall"],
  ["initial_state_fidelity", "Initial State"],
  ["mistake_authenticity", "Mistake Auth."],
  ["scaffolding_uptake", "Uptake"],
  ["kc_transition_consistency", "KC Transition"],
  ["learning_trajectory_plausibility", "Trajectory"],
  ["over_competence_control", "Over-Competence Control"],
] as const;

export function ScoreGrid({ scores }: { scores: Record<string, unknown> | null }) {
  return (
    <div className="score-grid">
      {fields.map(([field, label]) => (
        <div className="score-card" key={field}>
          <span>{label}</span>
          <strong>{scores ? String(scores[field] ?? "--") : "--"}</strong>
        </div>
      ))}
    </div>
  );
}
