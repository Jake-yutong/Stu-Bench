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

8. Click `Run selected`.

9. Confirm the dialogue timeline, score cards, judge rationale, and exports populate.

## Real Provider Connection Test

Use OpenAI, DeepSeek, Qwen, or Custom provider with base URL, model, API key, and
temperature. The connection test sends a minimal request before running an
episode.

## Research Notes

The app simulates each episode turn by turn. It resets conversation history
between episodes. SCS is never allowed to contain ground-truth answer, full real
trajectory, or judge rubric.

The v1 reward model is LLM-as-judge. Formula metric fields preserve the research
slots for KTS, uptake, and over-improvement, but `judge_estimated` values must
not be treated as human-verified annotations.
