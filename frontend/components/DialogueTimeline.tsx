interface Turn {
  turn_index: number;
  tutor_message: string;
  student_response: string;
}

export function DialogueTimeline({
  turns,
  labels = {
    ariaLabel: "Dialogue timeline",
    emptyTutor: "Tutor: Select an episode and start a run.",
    emptyStudent: "Student responses will appear one turn at a time.",
    tutorPrefix: "Tutor",
    studentPrefix: "Student",
  },
}: {
  turns: Turn[];
  labels?: {
    ariaLabel: string;
    emptyTutor: string;
    emptyStudent: string;
    tutorPrefix: string;
    studentPrefix: string;
  };
}) {
  return (
    <div className="timeline" aria-label={labels.ariaLabel}>
      {turns.length === 0 ? (
        <>
          <div className="turn tutor">{labels.emptyTutor}</div>
          <div className="turn student">{labels.emptyStudent}</div>
        </>
      ) : (
        turns.map((turn) => (
          <div key={turn.turn_index} className="turn-group">
            <div className="turn tutor">
              {labels.tutorPrefix}: {turn.tutor_message}
            </div>
            <div className="turn student">
              {labels.studentPrefix}: {turn.student_response}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
