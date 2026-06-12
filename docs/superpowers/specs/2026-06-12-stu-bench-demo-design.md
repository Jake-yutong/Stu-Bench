# Stu-Bench Demo Design

Date: 2026-06-12

## Goal

Build a local-first research demo for Stu-Bench, a benchmark for evaluating LLM-simulated students in scaffolded tutoring interactions. The demo will support a 20-episode pre-experiment from `Eedi/Question-Anchored-Tutoring-Dialogues-2k`, a usable interactive frontend, a computation backend, OpenAI-compatible model providers, LLM-as-judge evaluation, and CSV/JSON result export.

The first release is a local research workbench. Its architecture should leave room for future deployment, but it will not implement multi-user auth, server-side key vaulting, persistent database storage, or job queues in v1.

## Source Materials

The design is based on:

- `Benchmark.pdf`
- `Stu-Bench.md`
- Local Eedi dataset found at:
  `/Users/liyutong/Documents/Codex/2026-06-02/dataset-curl-lssf-https-hf-co/datasets/Eedi__Question-Anchored-Tutoring-Dialogues-2k`

Observed local dataset files include:

- `anchored-dialogues/train.csv`
- `anchored-dialogues/test.csv`
- `dq-question-metadata.csv`
- `dialogue-subjects.csv`

The dialogue table has fields such as `InterventionId`, `TutorId`, `QuestionId_DQ`, `MessageSequence`, `IsTutor`, `MessageString`, and `TalkMovePrediction`. The question metadata table is in long form, with `Label` identifying question text and answer option rows.

## Chosen Approach

Use the local-first research workbench approach:

- Frontend: Next.js / React.
- Backend: FastAPI / Python.
- Data: a prepared `demo_episodes.json` file with 20 structured LCS records.
- Providers: one OpenAI-compatible chat completions adapter with presets for OpenAI, DeepSeek, Qwen, and custom endpoints.
- Execution: sequential batch runner with live progress and a single-episode debug run option.
- Evaluation: LLM-as-judge at episode level by default, with schema space for later turn-level evaluation.
- Output: web results table, CSV export, JSON export.

This approach balances pre-experiment reliability, interactive demonstration quality, and future extensibility.

## System Architecture

### Frontend

The frontend is a dense research workbench with three main columns:

- Setup column:
  API provider configuration for the tested student model and the judge model, provider presets, base URL, API key, model name, temperature, test connection buttons, mode selector, episode selector, and run controls.
- Episode column:
  Question stem, answer options, SCS summary, scaffold sequence, live turn-by-turn dialogue timeline, compact run state, and progress indicator.
- Results column:
  Overall realism, six diagnostic dimension scores, judge rationale, failure flags, run metadata, CSV export, and JSON export.

The frontend must support light and dark mode. Layout and typography are part of acceptance criteria, not cosmetic follow-up work.

### Backend

The backend exposes a FastAPI service with these modules:

- `data_service`:
  Loads `demo_episodes.json`, validates LCS/SCS/ECS schema, and serves episode summaries/details.
- `prompt_service`:
  Builds Roleplay, Profile, and Context-Engineered message payloads from the same LCS.
- `provider_adapter`:
  Calls OpenAI-compatible Chat Completions APIs for OpenAI, DeepSeek, Qwen, and custom provider settings.
- `runner`:
  Runs selected episodes sequentially, performs turn-by-turn student model calls, emits progress state, isolates episode memory, and stores trajectories.
- `judge_service`:
  Calls the judge model with evaluator-facing context and generated trajectory, producing structured scores and rationale.
- `export_service`:
  Persists run JSON and generates CSV rows for downstream analysis.

### API Surface

Initial backend endpoints:

- `GET /api/episodes`
- `GET /api/episodes/{episode_id}`
- `POST /api/providers/test`
- `POST /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/events`
- `GET /api/runs/{run_id}/export.csv`
- `GET /api/runs/{run_id}/export.json`

The first implementation can use in-memory run state plus local JSON files. The service boundary should allow later replacement with database-backed state and a queued worker.

## Data Design

### LCS Is Structured Context Engineering

The Learner Context Set is a structured research object, not merely a long prompt. Each selected episode becomes one LCS record. The LCS is split into:

### SCS: Student-Facing Context Set

SCS is visible to the tested student model. It contains:

- Episode/question metadata.
- Problem text and answer options.
- Visible learner profile.
- Initial learner state abstraction.
- Current confusion or misconception abstraction.
- Language style guidance.
- KC state abstraction.
- Tutor scaffold sequence or current scaffold.
- Compact dialogue history within the current episode.

SCS must not contain:

- Ground-truth answer.
- Real student full trajectory.
- Evaluator rubric.
- ECS-only fields.

### ECS: Evaluator-Facing Context Set

ECS is visible only to judge/evaluation logic. It contains:

- Ground-truth answer.
- Real student trajectory.
- Tutor scaffold annotations.
- Reference or estimated KC transitions.
- Misconception path.
- Uptake evidence.
- Evaluation rubric.
- Expected failure modes such as over-competence or mechanical agreement.

### Demo Episode Generation

The demo will use a stable prepared file, `demo_episodes.json`, generated during development from the local Eedi dataset.

The preparation script should:

- Select 20 complete tutoring episodes suitable for demo use.
- Prefer episodes with enough turns to show scaffolded interaction.
- Join dialogue rows with question metadata and subject hierarchy.
- Build structured LCS records.
- Split student-visible SCS from evaluator-visible ECS.
- Preserve enough raw references to audit how the record was derived.

The frontend may show SCS/ECS summaries for inspection, but runtime behavior should load prepared records rather than regenerating annotations every time the app starts.

## Prompt Modes

The demo supports three testing modes, all derived from the same LCS:

### Roleplay Prompt

The weakest baseline. It gives the tested model only the role instruction and the problem context. It does not provide detailed learner state, KC state, real trajectory, or structured scaffold context.

### Profile Prompt

The intermediate baseline. It gives the tested model the problem plus a static learner profile and initial ability/confusion description. It does not provide the full structured SCS dynamics.

### Context-Engineered SCS

The proposed method. It gives the tested model the student-facing SCS fields, current tutor scaffold, and compact dialogue history. This is the main Stu-Bench condition.

## Experiment Protocol

The demo must simulate dialogue turn by turn.

For each episode:

1. Initialize a fresh conversation state.
2. Load the selected episode LCS.
3. Derive the current visible context according to the selected mode.
4. Present the next tutor scaffold.
5. Call the tested student model to generate one student response.
6. Append that response to the current episode's dialogue history.
7. Repeat until the scaffold sequence ends or the episode stop condition is reached.
8. Submit the generated trajectory plus ECS to the judge model.
9. Persist the episode result.

The student model must not be asked to generate the whole trajectory in one call.

When moving to the next episode:

- Clear all previous tutor/student messages.
- Clear compact dialogue history.
- Clear prompt cache for the previous episode.
- Reuse only experiment configuration such as model, provider, temperature, and mode.

This prevents cross-episode memory from contaminating results.

## Provider Configuration

Use a single OpenAI-compatible configuration model:

- Provider preset: OpenAI, DeepSeek, Qwen, or Custom.
- Base URL.
- API key.
- Model name.
- Temperature.

The frontend has separate configurations for:

- Tested student model.
- Judge model.

API key behavior:

- Keys are entered in the frontend.
- By default, keys are held only for the current browser session.
- A visible "remember on this device" toggle may save local configuration in browser storage.
- The default is not to persist keys.

Connection testing:

- `POST /api/providers/test` sends a minimal low-token request.
- It reports whether the provider/model is reachable and returns a readable error when not.

## Evaluation Design

The v1 reward model is LLM-as-judge. It should produce structured JSON rather than free-form prose only.

Each episode-level judge output includes:

- `overall_realism`
- `initial_state_fidelity`
- `mistake_authenticity`
- `scaffolding_uptake`
- `kc_transition_consistency`
- `learning_trajectory_plausibility`
- `over_competence_control`
- `judge_rationale`
- `failure_flags`
- `metric_status`

Scores use a 0-100 numeric scale, where higher is better for all realism dimensions. `over_competence_control` is also higher-is-better: a high value means the model successfully avoids over-competence.

### Formula-Based Metrics

The schema and code should preserve the research metrics from the proposal:

- KC Transition Similarity:
  `KTS_q = 1 - (1 / ((T_q - 1)K_q)) * sum_t sum_k |Delta m_t,k^(LLM) - Delta m_t,k^(Human)|`
- Scaffolding Uptake:
  `Uptake_q = (1 / |S_q|) * sum_{t in S_q} I(u_t = 1)`
- Over-improvement:
  `OverImprove_q = (1 / |S_q|) * sum_{t in S_q} I(o_t = 1)`

Because v1 may not have human-verified turn-level KC annotations for all 20 episodes, metric fields must distinguish:

- `computed`: calculated from available structured annotation.
- `judge_estimated`: derived from judge-produced per-turn indicators or state estimates.
- `pending_annotation`: schema field exists but reliable computation is not yet available.

The app must not present judge-estimated metrics as human-verified ground truth.

## Result Model and Export

The run JSON stores:

- Run configuration.
- Provider/model/mode metadata.
- Episode IDs.
- SCS summary used for the student model.
- Generated turn-by-turn trajectory.
- Judge input summary.
- Judge output.
- Formula metric fields and status.
- Errors, retries, and failure flags.

The CSV export uses one row per model/mode/episode result. It includes:

- Run ID.
- Timestamp.
- Episode ID.
- Question ID.
- Intervention ID.
- Mode.
- Student provider/model.
- Judge provider/model.
- Temperature settings.
- Overall realism.
- Six diagnostic scores.
- Formula metric fields where available.
- Metric status.
- Success/failure status.
- Error message if failed.

The UI table supports sorting/filtering by model, mode, episode, score, status, and failure flags.

## Frontend Visual Requirements

The workbench must be visually robust:

- Light and dark mode are supported.
- Text and background colors must have clear contrast in both modes.
- Avoid dark text on dark backgrounds and pale text on pale backgrounds.
- Buttons, inputs, toolbars, counters, and score cards must have stable dimensions.
- Long question text, prompt text, dialogue turns, and judge rationale must use scroll containers, truncation, or expandable regions.
- Components and text must not overlap on desktop or mobile.
- The desktop layout uses three columns.
- Smaller viewports can collapse into tabs or stacked panels.
- The first screen is the actual research workbench, not a marketing landing page.

## Error Handling

Expected failures:

- Missing API key.
- Provider connection failure.
- Model not found.
- Rate limit or timeout.
- Non-JSON judge response.
- Episode-level generation failure.
- Export write failure.

Behavior:

- Show clear error messages in the UI.
- Mark failed episode rows without stopping the entire batch.
- Retry transient provider failures a small bounded number of times.
- Preserve partial successful results.
- Keep run state inspectable after failure.

## Testing and Verification

Backend/data tests:

- Validate the 20-episode schema.
- Verify SCS does not contain answer, real student full trajectory, or judge rubric.
- Verify ECS contains evaluator-only fields.
- Verify all three modes derive from the same LCS.
- Verify provider config validation.
- Verify CSV and JSON export schemas.

Protocol tests:

- Verify student model calls are turn-by-turn.
- Verify a new episode starts with clean conversation history.
- Verify a failed episode does not contaminate later episodes.
- Verify judge calls receive ECS plus generated trajectory, not student-facing-only payloads.

Frontend tests:

- API forms.
- Provider presets.
- Connection tests.
- Mode selector.
- Episode viewer.
- Live dialogue timeline.
- Results table.
- Export buttons.
- Light/dark mode.

Visual QA:

- Use browser screenshots for desktop and mobile widths.
- Check contrast.
- Check no overlapping text.
- Check no button label overflow.
- Check long text containment.

Run acceptance:

- Mock provider can run all 20 episodes without real API cost.
- Real provider connection test can run with a small token budget.
- With valid keys, at least one full episode can run through student generation, judge scoring, table display, and export.

## Out of Scope for V1

- Training a real reward model.
- Multi-user hosted deployment.
- User accounts.
- Server-side API key vault.
- Database persistence.
- Distributed workers or queued cloud jobs.
- Full human annotation workflow for the complete benchmark.
- Automatically claiming formula metrics are human-verified when only judge estimates exist.

## Implementation Notes

The repository should eventually be placed at `Jake-yutong/Stu-Bench.git`. Network access to GitHub was not available during design exploration, so the local spec is written in this workspace first.

The next phase should create a detailed implementation plan before scaffolding code.
