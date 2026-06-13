# Real API Pre-Experiment Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the web demo practical for real API pre-experiments by adding provider connection testing, export buttons, and non-blocking long-run progress.

**Architecture:** Keep the local-first FastAPI + Next.js structure. Add an in-process async run manager for local demo progress without Redis/Celery, and let the frontend poll `/api/runs/{run_id}/events` until the run completes before loading result details.

**Tech Stack:** FastAPI, asyncio, Pydantic, pytest, Next.js, React, TypeScript, Vitest, Playwright.

---

## File Structure

- Modify `backend/app/api/runs.py`: return run metadata immediately, expose events for queued/running/completed/failed state.
- Create `backend/app/services/run_manager.py`: own in-memory progress state, background task scheduling, episode loop, and result persistence.
- Modify `backend/app/services/export_service.py`: make missing run files raise a predictable error instead of raw filesystem errors.
- Modify `backend/tests/test_exports.py`: cover async run start, progress events, result loading, exports, and unknown run behavior.
- Modify `frontend/lib/types.ts`: add provider test response, run status/events, and stronger run payload fields.
- Modify `frontend/lib/api.ts`: add `apiDownloadUrl`.
- Modify `frontend/components/EpisodeWorkbench.tsx`: wire connection tests, async run polling, progress display, result loading, and run id.
- Modify `frontend/components/ResultsPanel.tsx`: enable export buttons only after a run id is available.
- Modify `frontend/tests/workbench.test.tsx`: cover connection tests, progress polling, and export buttons.
- Modify `docs/demo-runbook.md`: document real API workflow and long-run polling.

## Tasks

### Task 1: Backend Async Run Manager

- [ ] Write failing backend tests showing `POST /api/runs` returns a queued/running run id immediately, `GET /events` reports progress, `GET /api/runs/{run_id}` returns persisted results after completion, unknown run ids return 404, and exports still work.
- [ ] Implement `run_manager.py` with `start_run`, `get_run_status`, `run_exists`, and background execution via `asyncio.create_task`.
- [ ] Update `runs.py` to use `run_manager`, map missing runs to 404, and keep CSV/JSON export behavior.
- [ ] Run `pytest backend/tests/test_exports.py -q` and `pytest backend/tests -q`.
- [ ] Commit as `feat: run experiments in background`.

### Task 2: Frontend Connection Tests, Progress, and Exports

- [ ] Write failing frontend tests for `Test connections`, progress polling after `Run selected`, final result rendering, and export link/button enablement.
- [ ] Extend frontend types and API helpers.
- [ ] Update `EpisodeWorkbench` to test both providers, start a run, poll events, load final result, and show progress.
- [ ] Update `ResultsPanel` to link CSV/JSON exports for the current run id and disable exports before a run exists.
- [ ] Run `npm test -- --run` and `bunx tsc --noEmit`.
- [ ] Commit as `feat: prepare frontend for real api runs`.

### Task 3: Verification, Visual QA, and Docs

- [ ] Update runbook with real API pre-experiment workflow and timeout notes.
- [ ] Run `npm run backend:test`, `npm test -- --run`, `bunx tsc --noEmit`, and `bun run visual`.
- [ ] Inspect the page in the in-app browser and verify mock run progress reaches completion.
- [ ] Commit docs or visual updates as needed.
- [ ] Push `feature/stu-bench-demo` to origin.

## Self-Review

- Connection testing is implemented in the frontend using the existing `/api/providers/test`.
- Exports use the existing backend export endpoints and become reachable from the frontend after a run id exists.
- Long runs are no longer a single blocking browser request; the frontend receives a run id and polls status.
- The design remains local-first and avoids introducing external infrastructure.
