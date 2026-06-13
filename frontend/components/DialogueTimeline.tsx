interface Turn {
  turn_index: number;
  tutor_message: string;
  student_response: string;
}

export function DialogueTimeline({ turns }: { turns: Turn[] }) {
  return (
    <div className="timeline" aria-label="Dialogue timeline">
      {turns.length === 0 ? (
        <>
          <div className="turn tutor">Tutor: Select an episode and start a run.</div>
          <div className="turn student">Student responses will appear one turn at a time.</div>
        </>
      ) : (
        turns.map((turn) => (
          <div key={turn.turn_index} className="turn-group">
            <div className="turn tutor">Tutor: {turn.tutor_message}</div>
            <div className="turn student">Student: {turn.student_response}</div>
          </div>
        ))
      )}
    </div>
  );
}
