# Local vLLM SFT/DPO Student Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add SFT and DPO fine-tuned student model options through an external OpenAI-compatible vLLM service while preventing Eedi2k train split leakage into demo episodes.

**Architecture:** Keep FastAPI as the orchestration layer and avoid loading 8B models in the web process. Treat SFT/DPO as student-provider presets that call a local vLLM OpenAI-compatible server at `http://127.0.0.1:8010/v1`, with `model` set to the LoRA adapter name. Regenerate/select demo episodes from the Eedi2k test split only.

**Tech Stack:** FastAPI, Pydantic, httpx, Next.js/React, Vitest, pytest, Playwright, external vLLM LoRA server.

---

### Task 1: Prevent Eedi2k Train Split Leakage

**Files:**
- Modify: `backend/scripts/prepare_demo_episodes.py`
- Test: `backend/tests/test_prepare_demo_episodes.py`

- [ ] Add a failing test proving `prepare()` reads `anchored-dialogues/test.csv` by default and ignores train-only episodes.
- [ ] Add a failing test or assertion that generated `backend/app/data/demo_episodes.json` episode IDs do not overlap the local train split when the dataset is available.
- [ ] Update `prepare()` to accept `split="test"` and default to `test.csv`.
- [ ] Run `pytest backend/tests/test_prepare_demo_episodes.py -q`.

### Task 2: Add Local vLLM Provider Presets

**Files:**
- Modify: `backend/app/data/schemas.py`
- Modify: `backend/app/services/provider_adapter.py`
- Test: `backend/tests/test_api.py`

- [ ] Add failing backend tests for `local_vllm_sft` and `local_vllm_dpo` provider defaults.
- [ ] Add failing backend tests that these presets post to `/chat/completions` with model names `eedi-stud-sft-8b` and `eedi-stud-dpo-8b`.
- [ ] Extend `ProviderPreset` and provider default URL/model helpers.
- [ ] Keep judge provider behavior unchanged; SFT/DPO are usable through the same OpenAI-compatible chat completion path.
- [ ] Run `pytest backend/tests/test_api.py -q`.

### Task 3: Add Frontend SFT/DPO Controls

**Files:**
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/components/ApiConfigPanel.tsx`
- Modify: `frontend/components/EpisodeWorkbench.tsx`
- Modify: `frontend/lib/i18n.ts`
- Test: `frontend/tests/workbench.test.tsx`

- [ ] Add failing frontend tests that selecting SFT/DPO fills the local vLLM base URL and adapter model names.
- [ ] Extend `ProviderPreset` and preset metadata in the API config panel.
- [ ] Show SFT/DPO presets for the student panel and keep judge presets API-compatible.
- [ ] Run `bun run test -- --run tests/workbench.test.tsx`.

### Task 4: Documentation and Verification

**Files:**
- Modify: `docs/demo-runbook.md`

- [ ] Document the vLLM LoRA serving command with `--enable-lora` and both adapter names.
- [ ] Document that demo episodes are test split only.
- [ ] Run `pytest backend/tests -q`.
- [ ] Run `bun run test -- --run`.
- [ ] Run `bunx tsc --noEmit`.
- [ ] Run `bun run visual` after frontend-visible changes.
