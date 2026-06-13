# Stu-Bench Demo Runbook

## Local Mock Run

1. Install backend dependencies:

```bash
pip install -e ".[dev]"
```

2. Install frontend dependencies:

```bash
cd frontend
bun install
```

If your local npm installation is healthy, `npm install` also works from the
`frontend` directory.

3. Start the backend:

```bash
python3 -m uvicorn backend.app.main:app --port 8000
```

4. Start the frontend:

```bash
cd frontend
bun run dev
```

5. Open `http://localhost:3000`.

6. Use `mock` for both Student API and Judge API.

7. Select `Context-Engineered SCS`.

8. Click `Test connections` and confirm both Student API and Judge API report
   `connection ok`.

9. Click `Run selected`.

10. Watch the progress line move through `queued`, `running`, and `completed`.

11. Confirm the dialogue timeline, score cards, judge rationale, and export links populate.

## Real Provider Connection Test

Use OpenAI, DeepSeek, Qwen, or Custom provider with base URL, model, API key, and
temperature. The connection test sends a minimal request before running an
episode.

Runs are submitted as background jobs. The browser polls
`/api/runs/{run_id}/events` for progress and fetches `/api/runs/{run_id}` only
after completion, so a long 20-episode pre-experiment is not held open by one
browser request. Provider calls have a backend timeout of 60 seconds per LLM
request; if a provider times out or returns an invalid response, the run records
that episode failure and keeps the result exportable.

After a run starts, the UI exposes CSV and JSON export links:

- `/api/runs/{run_id}/export.csv`
- `/api/runs/{run_id}/export.json`

## Research Notes

The app simulates each episode turn by turn. It resets conversation history
between episodes. SCS is never allowed to contain ground-truth answer, full real
trajectory, or judge rubric.

The v1 reward model is LLM-as-judge. Formula metric fields preserve the research
slots for KTS, uptake, and over-improvement, but `judge_estimated` values must
not be treated as human-verified annotations.
