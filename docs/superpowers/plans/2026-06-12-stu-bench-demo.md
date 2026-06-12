# Stu-Bench Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first Stu-Bench research workbench that runs 20 Eedi tutoring episodes through Roleplay, Profile, and Context-Engineered SCS modes, evaluates trajectories with LLM-as-judge, and exports CSV/JSON results.

**Architecture:** Use a monorepo with a FastAPI backend and a Next.js frontend. The backend owns LCS/SCS/ECS data loading, prompt construction, provider calls, turn-by-turn execution, judge scoring, and exports; the frontend owns API configuration, episode inspection, live progress, result tables, and light/dark visual quality.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest, httpx, pandas, Next.js, React, TypeScript, Tailwind CSS, Vitest or Jest, Playwright for visual QA.

---

## File Structure

Create this repository structure:

```text
.
├── README.md
├── package.json
├── pyproject.toml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── episodes.py
│   │   │   ├── providers.py
│   │   │   └── runs.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── errors.py
│   │   ├── data/
│   │   │   ├── demo_episodes.json
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── data_service.py
│   │   │   ├── export_service.py
│   │   │   ├── judge_service.py
│   │   │   ├── prompt_service.py
│   │   │   ├── provider_adapter.py
│   │   │   └── runner.py
│   │   └── storage/
│   │       └── runs/.gitkeep
│   ├── scripts/
│   │   └── prepare_demo_episodes.py
│   └── tests/
│       ├── fixtures/
│       │   └── tiny_episode.json
│       ├── test_api.py
│       ├── test_data_schema.py
│       ├── test_exports.py
│       ├── test_prompt_modes.py
│       ├── test_provider_adapter.py
│       └── test_runner_protocol.py
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ApiConfigPanel.tsx
│   │   ├── DialogueTimeline.tsx
│   │   ├── EpisodeWorkbench.tsx
│   │   ├── ResultsPanel.tsx
│   │   ├── ScoreGrid.tsx
│   │   └── ThemeToggle.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── storage.ts
│   └── tests/
│       ├── workbench.test.tsx
│       └── visual.spec.ts
└── docs/
    └── superpowers/
        ├── plans/2026-06-12-stu-bench-demo.md
        └── specs/2026-06-12-stu-bench-demo-design.md
```

Responsibilities:

- `backend/app/data/schemas.py`: canonical Pydantic schemas for LCS, SCS, ECS, runs, judge results, provider configs, and exports.
- `backend/app/services/data_service.py`: load and validate prepared demo episodes.
- `backend/scripts/prepare_demo_episodes.py`: build `demo_episodes.json` from local Eedi files.
- `backend/app/services/prompt_service.py`: derive Roleplay, Profile, and Context-Engineered message lists from the same LCS.
- `backend/app/services/provider_adapter.py`: OpenAI-compatible adapter plus mock provider.
- `backend/app/services/runner.py`: turn-by-turn episode execution and memory isolation.
- `backend/app/services/judge_service.py`: structured LLM-as-judge call and fallback validation.
- `backend/app/services/export_service.py`: local JSON persistence and CSV/JSON export.
- `frontend/components/*`: small focused UI components with stable layout constraints.
- `frontend/lib/api.ts`: typed client for backend endpoints.
- `frontend/lib/storage.ts`: session-only API key handling with explicit remember-on-device opt-in.

## Task 1: Repository Tooling and Baseline App Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `package.json`
- Create: `README.md`
- Create: `backend/app/main.py`
- Create: `backend/app/api/episodes.py`
- Create: `backend/app/api/providers.py`
- Create: `backend/app/api/runs.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/errors.py`
- Create: `backend/app/storage/runs/.gitkeep`
- Create: `backend/tests/test_api.py`

- [ ] **Step 1: Write the failing API health test**

Create `backend/tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint_returns_ok():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "stu-bench-demo"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
pytest backend/tests/test_api.py::test_health_endpoint_returns_ok -v
```

Expected: FAIL because `backend.app.main` or `/api/health` does not exist.

- [ ] **Step 3: Add backend package skeleton**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import episodes, providers, runs

app = FastAPI(title="Stu-Bench Demo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "stu-bench-demo"}


app.include_router(episodes.router, prefix="/api/episodes", tags=["episodes"])
app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
```

Create `backend/app/api/episodes.py`:

```python
from fastapi import APIRouter

router = APIRouter()
```

Create `backend/app/api/providers.py`:

```python
from fastapi import APIRouter

router = APIRouter()
```

Create `backend/app/api/runs.py`:

```python
from fastapi import APIRouter

router = APIRouter()
```

Create `backend/app/core/config.py`:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"
DATA_DIR = BACKEND_ROOT / "app" / "data"
RUN_STORAGE_DIR = BACKEND_ROOT / "app" / "storage" / "runs"
DEMO_EPISODES_PATH = DATA_DIR / "demo_episodes.json"
```

Create `backend/app/core/errors.py`:

```python
class StuBenchError(Exception):
    """Base application error for predictable API failures."""
```

Create `backend/app/storage/runs/.gitkeep` as an empty file.

- [ ] **Step 4: Add project config**

Create `pyproject.toml`:

```toml
[project]
name = "stu-bench-demo"
version = "0.1.0"
description = "Local-first Stu-Bench research demo"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.111",
  "uvicorn[standard]>=0.30",
  "pydantic>=2.7",
  "httpx>=0.27",
  "pandas>=2.2",
  "pyarrow>=16.0",
  "python-dotenv>=1.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2",
  "pytest-asyncio>=0.23",
  "ruff>=0.5"
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["backend/tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

Create root `package.json`:

```json
{
  "scripts": {
    "backend:dev": "uvicorn backend.app.main:app --reload --port 8000",
    "backend:test": "pytest backend/tests -q",
    "frontend:dev": "cd frontend && npm run dev",
    "frontend:test": "cd frontend && npm test",
    "lint:py": "ruff check backend",
    "test": "pytest backend/tests -q"
  }
}
```

Create `README.md`:

````markdown
# Stu-Bench Demo

Local-first research workbench for evaluating LLM-simulated students in scaffolded tutoring interactions.

## Development

Backend:

```bash
pip install -e ".[dev]"
npm run backend:dev
```

Tests:

```bash
npm run backend:test
```
````

- [ ] **Step 5: Run health test**

Run:

```bash
pytest backend/tests/test_api.py::test_health_endpoint_returns_ok -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml package.json README.md backend
git commit -m "chore: scaffold backend app"
```

## Task 2: Canonical LCS/SCS/ECS and Run Schemas

**Files:**
- Create: `backend/app/data/schemas.py`
- Create: `backend/tests/fixtures/tiny_episode.json`
- Create: `backend/tests/test_data_schema.py`

- [ ] **Step 1: Write schema tests first**

Create `backend/tests/fixtures/tiny_episode.json`:

```json
{
  "episode_id": "demo-001",
  "intervention_id": 10,
  "question_id": 104614,
  "subject": "Number",
  "topic": "Rounding and Estimating",
  "problem": {
    "text": "Who is correct when rounding 5.4598?",
    "answer_options": [
      {"label": "A", "text": "Only Alex"},
      {"label": "B", "text": "Only Sophie"},
      {"label": "C", "text": "Both Alex and Sophie"},
      {"label": "D", "text": "Neither Alex nor Sophie"}
    ]
  },
  "lcs": {
    "kc_components": [
      {"id": "kc-rounding-place-value", "description": "Round decimals to a requested place value"}
    ],
    "scaffold_sequence": [
      {"turn_id": "t1", "type": "questioning", "support_level": 1, "message": "What digit should we inspect for 1 decimal place?"}
    ],
    "scs": {
      "visible_learner_profile": "A Year 7 learner who answers briefly and is unsure about decimal place value.",
      "initial_learner_state": "Partially understands rounding but confuses which digit controls the decision.",
      "current_confusion": "May round 5.4598 to 5.4 when asked for one decimal place.",
      "language_style": "Short, tentative, student-like responses.",
      "kc_state_abstraction": [
        {"kc_id": "kc-rounding-place-value", "state": "partial"}
      ]
    },
    "ecs": {
      "ground_truth_answer": "C",
      "real_student_trajectory": [
        {"turn_index": 1, "speaker": "tutor", "message": "Hello Lina, just wanted to check, you OK?"},
        {"turn_index": 2, "speaker": "student", "message": "Hi I would you preferred to be called Lina Chen"}
      ],
      "reference_kc_transitions": [
        {"turn_index": 1, "states": [{"kc_id": "kc-rounding-place-value", "value": 0.5}]}
      ],
      "misconception_path": "Confuses decimal place inspected during rounding.",
      "uptake_evidence": "Student should revise based on digit inspection prompt.",
      "evaluation_rubric": "Reward gradual, scaffold-linked improvement and penalize expert-like leaps."
    }
  }
}
```

Create `backend/tests/test_data_schema.py`:

```python
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.data.schemas import EpisodeRecord


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def test_episode_record_validates_tiny_fixture():
    payload = json.loads(FIXTURE.read_text())
    episode = EpisodeRecord.model_validate(payload)
    assert episode.episode_id == "demo-001"
    assert episode.lcs.scs.visible_learner_profile.startswith("A Year 7")
    assert episode.lcs.ecs.ground_truth_answer == "C"


def test_scs_rejects_ground_truth_answer_leakage():
    payload = json.loads(FIXTURE.read_text())
    payload["lcs"]["scs"]["ground_truth_answer"] = "C"
    with pytest.raises(ValidationError):
        EpisodeRecord.model_validate(payload)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_data_schema.py -v
```

Expected: FAIL because `backend.app.data.schemas` does not exist.

- [ ] **Step 3: Implement schemas**

Create `backend/app/data/schemas.py`:

```python
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProviderPreset(str, Enum):
    openai = "openai"
    deepseek = "deepseek"
    qwen = "qwen"
    custom = "custom"
    mock = "mock"


class TestMode(str, Enum):
    roleplay = "roleplay"
    profile = "profile"
    context_engineered = "context_engineered"


class MetricStatus(str, Enum):
    computed = "computed"
    judge_estimated = "judge_estimated"
    pending_annotation = "pending_annotation"


class AnswerOption(StrictBaseModel):
    label: str
    text: str


class Problem(StrictBaseModel):
    text: str
    answer_options: list[AnswerOption] = Field(default_factory=list)


class KCComponent(StrictBaseModel):
    id: str
    description: str


class KCStateAbstraction(StrictBaseModel):
    kc_id: str
    state: Literal["confused", "partial", "mastered", "unknown"]


class ScaffoldTurn(StrictBaseModel):
    turn_id: str
    type: str
    support_level: int = Field(ge=0, le=3)
    message: str


class StudentFacingContext(StrictBaseModel):
    visible_learner_profile: str
    initial_learner_state: str
    current_confusion: str
    language_style: str
    kc_state_abstraction: list[KCStateAbstraction]


class DialogueTurn(StrictBaseModel):
    turn_index: int
    speaker: Literal["tutor", "student"]
    message: str


class KCStateValue(StrictBaseModel):
    kc_id: str
    value: float = Field(ge=0.0, le=1.0)


class KCTransition(StrictBaseModel):
    turn_index: int
    states: list[KCStateValue]


class EvaluatorFacingContext(StrictBaseModel):
    ground_truth_answer: str
    real_student_trajectory: list[DialogueTurn]
    reference_kc_transitions: list[KCTransition] = Field(default_factory=list)
    misconception_path: str
    uptake_evidence: str
    evaluation_rubric: str


class LearnerContextSet(StrictBaseModel):
    kc_components: list[KCComponent]
    scaffold_sequence: list[ScaffoldTurn]
    scs: StudentFacingContext
    ecs: EvaluatorFacingContext


class EpisodeRecord(StrictBaseModel):
    episode_id: str
    intervention_id: int
    question_id: int
    subject: str | None = None
    topic: str | None = None
    problem: Problem
    lcs: LearnerContextSet


class ProviderConfig(StrictBaseModel):
    preset: ProviderPreset
    base_url: str
    api_key: str
    model: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class RunConfig(StrictBaseModel):
    mode: TestMode
    student_provider: ProviderConfig
    judge_provider: ProviderConfig
    episode_ids: list[str]


class GeneratedTurn(StrictBaseModel):
    turn_index: int
    tutor_message: str
    student_response: str


class FormulaMetrics(StrictBaseModel):
    kts: float | None = None
    uptake: float | None = None
    over_improve: float | None = None
    status: MetricStatus


class JudgeScores(StrictBaseModel):
    overall_realism: int = Field(ge=0, le=100)
    initial_state_fidelity: int = Field(ge=0, le=100)
    mistake_authenticity: int = Field(ge=0, le=100)
    scaffolding_uptake: int = Field(ge=0, le=100)
    kc_transition_consistency: int = Field(ge=0, le=100)
    learning_trajectory_plausibility: int = Field(ge=0, le=100)
    over_competence_control: int = Field(ge=0, le=100)
    judge_rationale: str
    failure_flags: list[str] = Field(default_factory=list)
    formula_metrics: FormulaMetrics


class EpisodeResult(StrictBaseModel):
    episode_id: str
    mode: TestMode
    status: Literal["succeeded", "failed"]
    generated_trajectory: list[GeneratedTurn] = Field(default_factory=list)
    judge_scores: JudgeScores | None = None
    error_message: str | None = None
```

- [ ] **Step 4: Run schema tests**

Run:

```bash
pytest backend/tests/test_data_schema.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/data/schemas.py backend/tests/fixtures/tiny_episode.json backend/tests/test_data_schema.py
git commit -m "feat: define LCS episode schemas"
```

## Task 3: Data Service and Prepared Demo Episode Fixture

**Files:**
- Create: `backend/app/data/demo_episodes.json`
- Create: `backend/app/services/data_service.py`
- Modify: `backend/app/api/episodes.py`
- Create: `backend/tests/test_api.py`

- [ ] **Step 1: Write data service and episode API tests**

Append to `backend/tests/test_api.py`:

```python
def test_list_episodes_returns_demo_summaries():
    client = TestClient(app)
    response = client.get("/api/episodes")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["episodes"]) >= 1
    first = payload["episodes"][0]
    assert {"episode_id", "question_id", "intervention_id", "problem_preview"} <= set(first)


def test_get_episode_returns_scs_but_not_ecs_by_default():
    client = TestClient(app)
    episode_id = client.get("/api/episodes").json()["episodes"][0]["episode_id"]
    response = client.get(f"/api/episodes/{episode_id}")
    assert response.status_code == 200
    payload = response.json()
    assert "scs" in payload["lcs"]
    assert "ecs" not in payload["lcs"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_api.py::test_list_episodes_returns_demo_summaries backend/tests/test_api.py::test_get_episode_returns_scs_but_not_ecs_by_default -v
```

Expected: FAIL because endpoints are not implemented.

- [ ] **Step 3: Add minimal prepared demo file**

Create `backend/app/data/demo_episodes.json` with an array containing the same episode object from `backend/tests/fixtures/tiny_episode.json`.

- [ ] **Step 4: Implement data service**

Create `backend/app/services/data_service.py`:

```python
import json
from functools import lru_cache
from pathlib import Path

from backend.app.core.config import DEMO_EPISODES_PATH
from backend.app.data.schemas import EpisodeRecord


class EpisodeNotFoundError(KeyError):
    pass


@lru_cache(maxsize=1)
def load_demo_episodes(path: Path = DEMO_EPISODES_PATH) -> tuple[EpisodeRecord, ...]:
    payload = json.loads(path.read_text())
    return tuple(EpisodeRecord.model_validate(item) for item in payload)


def list_episode_summaries() -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for episode in load_demo_episodes():
        summaries.append(
            {
                "episode_id": episode.episode_id,
                "question_id": episode.question_id,
                "intervention_id": episode.intervention_id,
                "subject": episode.subject,
                "topic": episode.topic,
                "problem_preview": episode.problem.text[:160],
                "scaffold_turns": len(episode.lcs.scaffold_sequence),
            }
        )
    return summaries


def get_episode(episode_id: str) -> EpisodeRecord:
    for episode in load_demo_episodes():
        if episode.episode_id == episode_id:
            return episode
    raise EpisodeNotFoundError(episode_id)


def public_episode_detail(episode: EpisodeRecord) -> dict[str, object]:
    return {
        "episode_id": episode.episode_id,
        "intervention_id": episode.intervention_id,
        "question_id": episode.question_id,
        "subject": episode.subject,
        "topic": episode.topic,
        "problem": episode.problem.model_dump(),
        "lcs": {
            "kc_components": [item.model_dump() for item in episode.lcs.kc_components],
            "scaffold_sequence": [item.model_dump() for item in episode.lcs.scaffold_sequence],
            "scs": episode.lcs.scs.model_dump(),
        },
    }
```

- [ ] **Step 5: Implement episode API**

Replace `backend/app/api/episodes.py`:

```python
from fastapi import APIRouter, HTTPException

from backend.app.services.data_service import (
    EpisodeNotFoundError,
    get_episode,
    list_episode_summaries,
    public_episode_detail,
)

router = APIRouter()


@router.get("")
def list_episodes() -> dict[str, object]:
    return {"episodes": list_episode_summaries()}


@router.get("/{episode_id}")
def read_episode(episode_id: str) -> dict[str, object]:
    try:
        episode = get_episode(episode_id)
    except EpisodeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Episode not found") from exc
    return public_episode_detail(episode)
```

- [ ] **Step 6: Run tests**

Run:

```bash
pytest backend/tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/data/demo_episodes.json backend/app/services/data_service.py backend/app/api/episodes.py backend/tests/test_api.py
git commit -m "feat: serve prepared demo episodes"
```

## Task 4: Eedi Preparation Script for 20 LCS Records

**Files:**
- Create: `backend/scripts/prepare_demo_episodes.py`
- Create: `backend/tests/test_prepare_demo_episodes.py`

- [ ] **Step 1: Write preparation unit tests**

Create `backend/tests/test_prepare_demo_episodes.py`:

```python
import pandas as pd

from backend.scripts.prepare_demo_episodes import build_episode_record, select_episode_ids


def test_select_episode_ids_prefers_dialogues_with_minimum_turns():
    short_dialogue = [
        {"InterventionId": 1, "QuestionId_DQ": 101, "MessageSequence": 1, "IsTutor": 1, "MessageString": "a", "TalkMovePrediction": "<None>"},
        {"InterventionId": 1, "QuestionId_DQ": 101, "MessageSequence": 2, "IsTutor": 0, "MessageString": "b", "TalkMovePrediction": None},
    ]
    long_dialogue = [
        {"InterventionId": 2, "QuestionId_DQ": 202, "MessageSequence": i, "IsTutor": i % 2, "MessageString": f"m{i}", "TalkMovePrediction": "hint"}
        for i in range(1, 13)
    ]
    dialogues = pd.DataFrame(short_dialogue + long_dialogue)
    selected = select_episode_ids(dialogues, count=1, min_turns=10)
    assert selected == [(2, 202)]


def test_build_episode_record_splits_scs_and_ecs():
    dialogue_rows = pd.DataFrame(
        [
            {"InterventionId": 10, "QuestionId_DQ": 104614, "MessageSequence": 1, "IsTutor": 1, "MessageString": "Tutor prompt", "TalkMovePrediction": "questioning"},
            {"InterventionId": 10, "QuestionId_DQ": 104614, "MessageSequence": 2, "IsTutor": 0, "MessageString": "Student answer", "TalkMovePrediction": None}
        ]
    )
    metadata = pd.DataFrame(
        [
            {"QuestionId_DQ": 104614, "InterventionId": 10, "Text": "Question text", "Sequence": 1, "Label": "Question Text"},
            {"QuestionId_DQ": 104614, "InterventionId": 10, "Text": "Only Alex", "Sequence": 2, "Label": "Answer A Text"},
            {"QuestionId_DQ": 104614, "InterventionId": 10, "Text": "Both", "Sequence": 4, "Label": "Answer C Text"}
        ]
    )
    subjects = pd.DataFrame(
        [
            {"InterventionId": 10, "SubjectName": "Number", "SubjectLevel": 1, "SubjectType": "Subject"},
            {"InterventionId": 10, "SubjectName": "Rounding", "SubjectLevel": 2, "SubjectType": "Topic"}
        ]
    )
    episode = build_episode_record((10, 104614), dialogue_rows, metadata, subjects)
    assert episode.lcs.scs.visible_learner_profile
    assert episode.lcs.ecs.real_student_trajectory[1].speaker == "student"
    assert "ground_truth_answer" not in episode.lcs.scs.model_dump()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_prepare_demo_episodes.py -v
```

Expected: FAIL because preparation script does not exist.

- [ ] **Step 3: Implement preparation script**

Create `backend/scripts/prepare_demo_episodes.py`:

```python
import argparse
import json
from pathlib import Path

import pandas as pd

from backend.app.data.schemas import (
    AnswerOption,
    DialogueTurn,
    EpisodeRecord,
    EvaluatorFacingContext,
    KCComponent,
    KCStateAbstraction,
    LearnerContextSet,
    Problem,
    ScaffoldTurn,
    StudentFacingContext,
)


ANSWER_LABELS = {
    "Answer A Text": "A",
    "Answer B Text": "B",
    "Answer C Text": "C",
    "Answer D Text": "D",
}


def select_episode_ids(dialogues: pd.DataFrame, count: int, min_turns: int) -> list[tuple[int, int]]:
    grouped = (
        dialogues.groupby(["InterventionId", "QuestionId_DQ"])
        .size()
        .reset_index(name="turn_count")
        .sort_values(["turn_count", "InterventionId", "QuestionId_DQ"], ascending=[False, True, True])
    )
    eligible = grouped[grouped["turn_count"] >= min_turns].head(count)
    return [(int(row.InterventionId), int(row.QuestionId_DQ)) for row in eligible.itertuples()]


def _question_text(metadata_rows: pd.DataFrame) -> str:
    matches = metadata_rows[metadata_rows["Label"] == "Question Text"].sort_values("Sequence")
    return str(matches.iloc[0]["Text"]) if not matches.empty else "Question text unavailable"


def _answer_options(metadata_rows: pd.DataFrame) -> list[AnswerOption]:
    options: list[AnswerOption] = []
    for row in metadata_rows.sort_values("Sequence").itertuples():
        label = ANSWER_LABELS.get(str(row.Label))
        if label:
            options.append(AnswerOption(label=label, text=str(row.Text)))
    return options


def _subject_topic(subject_rows: pd.DataFrame) -> tuple[str | None, str | None]:
    subject = None
    topic = None
    for row in subject_rows.sort_values("SubjectLevel").itertuples():
        if row.SubjectType == "Subject" and subject is None:
            subject = str(row.SubjectName)
        if row.SubjectType == "Topic" and topic is None:
            topic = str(row.SubjectName)
    return subject, topic


def build_episode_record(
    key: tuple[int, int],
    dialogue_rows: pd.DataFrame,
    metadata: pd.DataFrame,
    subjects: pd.DataFrame,
) -> EpisodeRecord:
    intervention_id, question_id = key
    rows = dialogue_rows[
        (dialogue_rows["InterventionId"] == intervention_id)
        & (dialogue_rows["QuestionId_DQ"] == question_id)
    ].sort_values("MessageSequence")
    metadata_rows = metadata[
        (metadata["InterventionId"] == intervention_id)
        & (metadata["QuestionId_DQ"] == question_id)
    ]
    subject_rows = subjects[subjects["InterventionId"] == intervention_id]
    subject, topic = _subject_topic(subject_rows)
    dialogue = [
        DialogueTurn(
            turn_index=int(row.MessageSequence),
            speaker="tutor" if int(row.IsTutor) == 1 else "student",
            message=str(row.MessageString),
        )
        for row in rows.itertuples()
    ]
    scaffold = [
        ScaffoldTurn(
            turn_id=f"t{idx + 1}",
            type=str(row.TalkMovePrediction) if pd.notna(row.TalkMovePrediction) else "tutor_message",
            support_level=1 if int(row.IsTutor) == 1 else 0,
            message=str(row.MessageString),
        )
        for idx, row in enumerate(rows[rows["IsTutor"] == 1].itertuples())
    ]
    topic_text = topic or subject or "mathematics"
    kc_id = f"kc-{topic_text.lower().replace(' ', '-')}"
    lcs = LearnerContextSet(
        kc_components=[KCComponent(id=kc_id, description=f"Reason about {topic_text}")],
        scaffold_sequence=scaffold[:8],
        scs=StudentFacingContext(
            visible_learner_profile="A lower-secondary learner responding in a brief, tentative style.",
            initial_learner_state="Derived from the beginning of a real tutoring episode; the learner may hold a partial or confused understanding.",
            current_confusion=f"Likely confusion connected to {topic_text}.",
            language_style="Short, natural student replies; avoid expert explanations unless scaffolded.",
            kc_state_abstraction=[KCStateAbstraction(kc_id=kc_id, state="partial")],
        ),
        ecs=EvaluatorFacingContext(
            ground_truth_answer="pending_annotation",
            real_student_trajectory=dialogue,
            reference_kc_transitions=[],
            misconception_path=f"Judge should infer misconception path from the real trajectory and {topic_text} context.",
            uptake_evidence="Use the real student trajectory and tutor scaffolds as reference evidence.",
            evaluation_rubric="Reward gradual, scaffold-linked learner realism. Penalize over-competence, irrelevant uptake, and mechanical agreement.",
        ),
    )
    return EpisodeRecord(
        episode_id=f"eedi-{intervention_id}-{question_id}",
        intervention_id=intervention_id,
        question_id=question_id,
        subject=subject,
        topic=topic,
        problem=Problem(text=_question_text(metadata_rows), answer_options=_answer_options(metadata_rows)),
        lcs=lcs,
    )


def prepare(input_dir: Path, output_path: Path, count: int = 20, min_turns: int = 10) -> list[EpisodeRecord]:
    dialogues = pd.read_csv(input_dir / "anchored-dialogues" / "train.csv")
    metadata = pd.read_csv(input_dir / "dq-question-metadata.csv")
    subjects = pd.read_csv(input_dir / "dialogue-subjects.csv")
    keys = select_episode_ids(dialogues, count=count, min_turns=min_turns)
    episodes = [build_episode_record(key, dialogues, metadata, subjects) for key in keys]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps([episode.model_dump() for episode in episodes], indent=2))
    return episodes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--min-turns", type=int, default=10)
    args = parser.parse_args()
    episodes = prepare(Path(args.input_dir), Path(args.output), args.count, args.min_turns)
    print(f"Wrote {len(episodes)} episodes to {args.output}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run preparation tests**

Run:

```bash
pytest backend/tests/test_prepare_demo_episodes.py -v
```

Expected: PASS.

- [ ] **Step 5: Generate 20 local demo episodes**

Run:

```bash
python backend/scripts/prepare_demo_episodes.py \
  --input-dir /Users/liyutong/Documents/Codex/2026-06-02/dataset-curl-lssf-https-hf-co/datasets/Eedi__Question-Anchored-Tutoring-Dialogues-2k \
  --output backend/app/data/demo_episodes.json \
  --count 20 \
  --min-turns 10
```

Expected: `Wrote 20 episodes to backend/app/data/demo_episodes.json`.

- [ ] **Step 6: Validate generated file**

Run:

```bash
python -c "from backend.app.services.data_service import load_demo_episodes; episodes=load_demo_episodes(); assert len(episodes)==20; assert all(not hasattr(e.lcs.scs, 'ground_truth_answer') for e in episodes); print(len(episodes))"
```

Expected: `20`.

- [ ] **Step 7: Commit**

```bash
git add backend/scripts/prepare_demo_episodes.py backend/tests/test_prepare_demo_episodes.py backend/app/data/demo_episodes.json
git commit -m "feat: prepare twenty Eedi demo episodes"
```

## Task 5: Prompt Builder for Three Testing Modes

**Files:**
- Create: `backend/app/services/prompt_service.py`
- Create: `backend/tests/test_prompt_modes.py`

- [ ] **Step 1: Write prompt mode tests**

Create `backend/tests/test_prompt_modes.py`:

```python
import json
from pathlib import Path

from backend.app.data.schemas import EpisodeRecord, TestMode
from backend.app.services.prompt_service import build_student_messages


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def _episode() -> EpisodeRecord:
    return EpisodeRecord.model_validate(json.loads(FIXTURE.read_text()))


def test_roleplay_prompt_excludes_profile_and_ecs():
    messages = build_student_messages(_episode(), TestMode.roleplay, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "You are simulating a student" in joined
    assert "ground_truth_answer" not in joined
    assert "evaluation_rubric" not in joined
    assert "visible_learner_profile" not in joined


def test_profile_prompt_includes_static_profile_but_not_ecs():
    messages = build_student_messages(_episode(), TestMode.profile, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "Visible learner profile" in joined
    assert "A Year 7 learner" in joined
    assert "ground_truth_answer" not in joined


def test_context_engineered_prompt_includes_scs_and_current_scaffold():
    messages = build_student_messages(_episode(), TestMode.context_engineered, [], "Tutor hint")
    joined = "\n".join(message["content"] for message in messages)
    assert "Student-facing Context Set" in joined
    assert "Tutor hint" in joined
    assert "ground_truth_answer" not in joined
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_prompt_modes.py -v
```

Expected: FAIL because `prompt_service.py` does not exist.

- [ ] **Step 3: Implement prompt builder**

Create `backend/app/services/prompt_service.py`:

```python
from backend.app.data.schemas import EpisodeRecord, GeneratedTurn, TestMode


ChatMessage = dict[str, str]


def _problem_block(episode: EpisodeRecord) -> str:
    options = "\n".join(
        f"{option.label}. {option.text}" for option in episode.problem.answer_options
    )
    return f"Problem:\n{episode.problem.text}\n\nAnswer options:\n{options}"


def _history_block(history: list[GeneratedTurn]) -> str:
    if not history:
        return "No previous generated turns in this episode."
    return "\n".join(
        f"Turn {turn.turn_index}\nTutor: {turn.tutor_message}\nStudent: {turn.student_response}"
        for turn in history
    )


def build_student_messages(
    episode: EpisodeRecord,
    mode: TestMode,
    history: list[GeneratedTurn],
    current_scaffold: str,
) -> list[ChatMessage]:
    system = (
        "You are simulating a lower-secondary mathematics student in a tutoring dialogue. "
        "Respond as the student only. Keep responses brief and natural. Do not reveal hidden evaluation logic."
    )
    problem = _problem_block(episode)
    history_text = _history_block(history)

    if mode == TestMode.roleplay:
        user = (
            f"{problem}\n\n"
            "You are simulating a student. Answer the tutor's next message as that student.\n\n"
            f"Episode history:\n{history_text}\n\n"
            f"Tutor message:\n{current_scaffold}"
        )
    elif mode == TestMode.profile:
        scs = episode.lcs.scs
        user = (
            f"{problem}\n\n"
            f"Visible learner profile: {scs.visible_learner_profile}\n"
            f"Initial learner state: {scs.initial_learner_state}\n"
            f"Current confusion: {scs.current_confusion}\n"
            f"Language style: {scs.language_style}\n\n"
            f"Episode history:\n{history_text}\n\n"
            f"Tutor message:\n{current_scaffold}"
        )
    else:
        scs = episode.lcs.scs
        kc_states = ", ".join(
            f"{item.kc_id}={item.state}" for item in scs.kc_state_abstraction
        )
        user = (
            f"{problem}\n\n"
            "Student-facing Context Set:\n"
            f"- Visible learner profile: {scs.visible_learner_profile}\n"
            f"- Initial learner state: {scs.initial_learner_state}\n"
            f"- Current confusion: {scs.current_confusion}\n"
            f"- Language style: {scs.language_style}\n"
            f"- KC state abstraction: {kc_states}\n\n"
            f"Episode history:\n{history_text}\n\n"
            f"Current tutor scaffold:\n{current_scaffold}\n\n"
            "Generate one student response only. Show plausible uptake only when the scaffold supports it."
        )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
```

- [ ] **Step 4: Run prompt tests**

Run:

```bash
pytest backend/tests/test_prompt_modes.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/prompt_service.py backend/tests/test_prompt_modes.py
git commit -m "feat: build student prompts from LCS modes"
```

## Task 6: Provider Adapter with Mock and OpenAI-Compatible Calls

**Files:**
- Create: `backend/app/services/provider_adapter.py`
- Modify: `backend/app/api/providers.py`
- Create: `backend/tests/test_provider_adapter.py`

- [ ] **Step 1: Write provider tests**

Create `backend/tests/test_provider_adapter.py`:

```python
import pytest

from backend.app.data.schemas import ProviderConfig, ProviderPreset
from backend.app.services.provider_adapter import chat_completion, provider_base_url


def test_provider_presets_resolve_base_urls():
    assert provider_base_url(ProviderPreset.openai) == "https://api.openai.com/v1"
    assert provider_base_url(ProviderPreset.deepseek) == "https://api.deepseek.com"
    assert provider_base_url(ProviderPreset.qwen) == "https://dashscope.aliyuncs.com/compatible-mode/v1"


@pytest.mark.asyncio
async def test_mock_provider_returns_deterministic_student_text():
    config = ProviderConfig(
        preset=ProviderPreset.mock,
        base_url="mock://local",
        api_key="mock",
        model="mock-student",
        temperature=0.4,
    )
    text = await chat_completion(config, [{"role": "user", "content": "Tutor message: Try rounding."}])
    assert "I think" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_provider_adapter.py -v
```

Expected: FAIL because provider adapter does not exist.

- [ ] **Step 3: Implement provider adapter**

Create `backend/app/services/provider_adapter.py`:

```python
import httpx

from backend.app.data.schemas import ProviderConfig, ProviderPreset


class ProviderError(RuntimeError):
    pass


def provider_base_url(preset: ProviderPreset) -> str:
    defaults = {
        ProviderPreset.openai: "https://api.openai.com/v1",
        ProviderPreset.deepseek: "https://api.deepseek.com",
        ProviderPreset.qwen: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ProviderPreset.mock: "mock://local",
        ProviderPreset.custom: "",
    }
    return defaults[preset]


async def chat_completion(config: ProviderConfig, messages: list[dict[str, str]]) -> str:
    if config.preset == ProviderPreset.mock:
        return _mock_response(config, messages)

    url = config.base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": 600,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=headers, json=payload)
    if response.status_code >= 400:
        raise ProviderError(f"Provider returned {response.status_code}: {response.text[:500]}")
    data = response.json()
    try:
        return str(data["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("Provider response did not contain choices[0].message.content") from exc


def _mock_response(config: ProviderConfig, messages: list[dict[str, str]]) -> str:
    joined = "\n".join(message["content"] for message in messages)
    if "JSON" in joined or "judge" in config.model.lower():
        return (
            '{"overall_realism": 78, "initial_state_fidelity": 76, '
            '"mistake_authenticity": 74, "scaffolding_uptake": 80, '
            '"kc_transition_consistency": 72, "learning_trajectory_plausibility": 79, '
            '"over_competence_control": 83, "judge_rationale": "Mock judge: plausible gradual uptake.", '
            '"failure_flags": [], "formula_metrics": {"kts": null, "uptake": null, '
            '"over_improve": null, "status": "judge_estimated"}}'
        )
    return "I think I understand part of it, but I need to check the next digit."
```

- [ ] **Step 4: Implement provider test endpoint**

Replace `backend/app/api/providers.py`:

```python
from fastapi import APIRouter, HTTPException

from backend.app.data.schemas import ProviderConfig
from backend.app.services.provider_adapter import ProviderError, chat_completion

router = APIRouter()


@router.post("/test")
async def test_provider(config: ProviderConfig) -> dict[str, object]:
    try:
        text = await chat_completion(
            config,
            [{"role": "user", "content": "Reply with exactly: connection ok"}],
        )
    except ProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "sample": text[:200]}
```

- [ ] **Step 5: Run provider tests**

Run:

```bash
pytest backend/tests/test_provider_adapter.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/provider_adapter.py backend/app/api/providers.py backend/tests/test_provider_adapter.py
git commit -m "feat: add OpenAI-compatible provider adapter"
```

## Task 7: Turn-by-Turn Runner with Episode Memory Isolation

**Files:**
- Create: `backend/app/services/runner.py`
- Create: `backend/tests/test_runner_protocol.py`

- [ ] **Step 1: Write runner protocol tests**

Create `backend/tests/test_runner_protocol.py`:

```python
import json
from pathlib import Path

import pytest

from backend.app.data.schemas import EpisodeRecord, ProviderConfig, ProviderPreset, TestMode
from backend.app.services.runner import run_episode


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def _episode() -> EpisodeRecord:
    return EpisodeRecord.model_validate(json.loads(FIXTURE.read_text()))


def _provider() -> ProviderConfig:
    return ProviderConfig(
        preset=ProviderPreset.mock,
        base_url="mock://local",
        api_key="mock",
        model="mock-student",
        temperature=0.7,
    )


@pytest.mark.asyncio
async def test_run_episode_calls_student_once_per_scaffold_turn():
    episode = _episode()
    result = await run_episode(episode, TestMode.context_engineered, _provider())
    assert result.status == "succeeded"
    assert len(result.generated_trajectory) == len(episode.lcs.scaffold_sequence)


@pytest.mark.asyncio
async def test_run_episode_starts_with_clean_history_each_time():
    episode = _episode()
    first = await run_episode(episode, TestMode.context_engineered, _provider())
    second = await run_episode(episode, TestMode.context_engineered, _provider())
    assert first.generated_trajectory[0].turn_index == 1
    assert second.generated_trajectory[0].turn_index == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_runner_protocol.py -v
```

Expected: FAIL because runner does not exist.

- [ ] **Step 3: Implement runner**

Create `backend/app/services/runner.py`:

```python
from backend.app.data.schemas import (
    EpisodeRecord,
    EpisodeResult,
    GeneratedTurn,
    ProviderConfig,
    TestMode,
)
from backend.app.services.prompt_service import build_student_messages
from backend.app.services.provider_adapter import ProviderError, chat_completion


async def run_episode(
    episode: EpisodeRecord,
    mode: TestMode,
    student_provider: ProviderConfig,
) -> EpisodeResult:
    history: list[GeneratedTurn] = []
    try:
        for index, scaffold in enumerate(episode.lcs.scaffold_sequence, start=1):
            messages = build_student_messages(episode, mode, history, scaffold.message)
            student_response = await chat_completion(student_provider, messages)
            history.append(
                GeneratedTurn(
                    turn_index=index,
                    tutor_message=scaffold.message,
                    student_response=student_response,
                )
            )
        return EpisodeResult(
            episode_id=episode.episode_id,
            mode=mode,
            status="succeeded",
            generated_trajectory=history,
        )
    except ProviderError as exc:
        return EpisodeResult(
            episode_id=episode.episode_id,
            mode=mode,
            status="failed",
            generated_trajectory=history,
            error_message=str(exc),
        )
```

- [ ] **Step 4: Run runner tests**

Run:

```bash
pytest backend/tests/test_runner_protocol.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/runner.py backend/tests/test_runner_protocol.py
git commit -m "feat: run episodes turn by turn"
```

## Task 8: Judge Service and Formula Metric Helpers

**Files:**
- Create: `backend/app/services/judge_service.py`
- Create: `backend/tests/test_judge_service.py`

- [ ] **Step 1: Write judge service tests**

Create `backend/tests/test_judge_service.py`:

```python
import json
from pathlib import Path

import pytest

from backend.app.data.schemas import EpisodeRecord, ProviderConfig, ProviderPreset, TestMode
from backend.app.services.judge_service import judge_episode
from backend.app.services.runner import run_episode


FIXTURE = Path(__file__).parent / "fixtures" / "tiny_episode.json"


def _episode() -> EpisodeRecord:
    return EpisodeRecord.model_validate(json.loads(FIXTURE.read_text()))


def _provider() -> ProviderConfig:
    return ProviderConfig(
        preset=ProviderPreset.mock,
        base_url="mock://local",
        api_key="mock",
        model="mock-judge",
        temperature=0.0,
    )


@pytest.mark.asyncio
async def test_judge_episode_returns_scores_on_0_to_100_scale():
    episode = _episode()
    result = await run_episode(episode, TestMode.context_engineered, _provider())
    judged = await judge_episode(episode, result, _provider())
    assert judged.judge_scores is not None
    assert judged.judge_scores.overall_realism == 78
    assert judged.judge_scores.formula_metrics.status == "judge_estimated"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_judge_service.py -v
```

Expected: FAIL because judge service does not exist.

- [ ] **Step 3: Implement judge service**

Create `backend/app/services/judge_service.py`:

```python
import json

from pydantic import ValidationError

from backend.app.data.schemas import EpisodeRecord, EpisodeResult, JudgeScores, ProviderConfig
from backend.app.services.provider_adapter import ProviderError, chat_completion


def build_judge_messages(episode: EpisodeRecord, result: EpisodeResult) -> list[dict[str, str]]:
    trajectory = [turn.model_dump() for turn in result.generated_trajectory]
    evaluator_context = episode.lcs.ecs.model_dump()
    rubric = (
        "Score each field from 0 to 100. Higher is better. "
        "over_competence_control is higher when the model avoids expert-like leaps. "
        "Return only JSON matching the requested keys."
    )
    return [
        {"role": "system", "content": "You are an evaluator for learner realism in scaffolded tutoring dialogues."},
        {
            "role": "user",
            "content": (
                f"{rubric}\n\n"
                f"Problem: {episode.problem.model_dump()}\n\n"
                f"Evaluator-facing context: {json.dumps(evaluator_context)}\n\n"
                f"Generated trajectory: {json.dumps(trajectory)}"
            ),
        },
    ]


async def judge_episode(
    episode: EpisodeRecord,
    result: EpisodeResult,
    judge_provider: ProviderConfig,
) -> EpisodeResult:
    if result.status == "failed":
        return result
    try:
        text = await chat_completion(judge_provider, build_judge_messages(episode, result))
        scores = JudgeScores.model_validate(json.loads(text))
        return result.model_copy(update={"judge_scores": scores})
    except (ProviderError, json.JSONDecodeError, ValidationError) as exc:
        return result.model_copy(update={"status": "failed", "error_message": f"Judge failed: {exc}"})
```

- [ ] **Step 4: Run judge tests**

Run:

```bash
pytest backend/tests/test_judge_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/judge_service.py backend/tests/test_judge_service.py
git commit -m "feat: score trajectories with judge service"
```

## Task 9: Run Orchestration API and Local Persistence

**Files:**
- Create: `backend/app/services/export_service.py`
- Modify: `backend/app/api/runs.py`
- Create: `backend/tests/test_exports.py`

- [ ] **Step 1: Write run API and export tests**

Create `backend/tests/test_exports.py`:

```python
from fastapi.testclient import TestClient

from backend.app.main import app


def _mock_provider(model: str) -> dict[str, object]:
    return {
        "preset": "mock",
        "base_url": "mock://local",
        "api_key": "mock",
        "model": model,
        "temperature": 0.2,
    }


def test_create_run_and_export_json_and_csv():
    client = TestClient(app)
    episode_id = client.get("/api/episodes").json()["episodes"][0]["episode_id"]
    response = client.post(
        "/api/runs",
        json={
            "mode": "context_engineered",
            "student_provider": _mock_provider("mock-student"),
            "judge_provider": _mock_provider("mock-judge"),
            "episode_ids": [episode_id],
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    run_payload = client.get(f"/api/runs/{run_id}").json()
    assert run_payload["results"][0]["status"] == "succeeded"
    csv_response = client.get(f"/api/runs/{run_id}/export.csv")
    assert csv_response.status_code == 200
    assert "overall_realism" in csv_response.text
    json_response = client.get(f"/api/runs/{run_id}/export.json")
    assert json_response.status_code == 200
    assert json_response.json()["run_id"] == run_id
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_exports.py -v
```

Expected: FAIL because run API is not implemented.

- [ ] **Step 3: Implement export service**

Create `backend/app/services/export_service.py`:

```python
import csv
import json
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from uuid import uuid4

from backend.app.core.config import RUN_STORAGE_DIR
from backend.app.data.schemas import EpisodeResult, RunConfig


def new_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"run-{timestamp}-{uuid4().hex[:8]}"


def persist_run(run_id: str, config: RunConfig, results: list[EpisodeResult]) -> dict[str, object]:
    RUN_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config.model_dump(mode="json"),
        "results": [result.model_dump(mode="json") for result in results],
    }
    (RUN_STORAGE_DIR / f"{run_id}.json").write_text(json.dumps(payload, indent=2))
    return payload


def load_run(run_id: str) -> dict[str, object]:
    return json.loads((RUN_STORAGE_DIR / f"{run_id}.json").read_text())


def run_to_csv(payload: dict[str, object]) -> str:
    output = StringIO()
    fieldnames = [
        "run_id",
        "episode_id",
        "mode",
        "status",
        "overall_realism",
        "initial_state_fidelity",
        "mistake_authenticity",
        "scaffolding_uptake",
        "kc_transition_consistency",
        "learning_trajectory_plausibility",
        "over_competence_control",
        "metric_status",
        "error_message",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for result in payload["results"]:
        scores = result.get("judge_scores") or {}
        formula = scores.get("formula_metrics") or {}
        writer.writerow(
            {
                "run_id": payload["run_id"],
                "episode_id": result["episode_id"],
                "mode": result["mode"],
                "status": result["status"],
                "overall_realism": scores.get("overall_realism"),
                "initial_state_fidelity": scores.get("initial_state_fidelity"),
                "mistake_authenticity": scores.get("mistake_authenticity"),
                "scaffolding_uptake": scores.get("scaffolding_uptake"),
                "kc_transition_consistency": scores.get("kc_transition_consistency"),
                "learning_trajectory_plausibility": scores.get("learning_trajectory_plausibility"),
                "over_competence_control": scores.get("over_competence_control"),
                "metric_status": formula.get("status"),
                "error_message": result.get("error_message"),
            }
        )
    return output.getvalue()
```

- [ ] **Step 4: Implement run API**

Replace `backend/app/api/runs.py`:

```python
from fastapi import APIRouter, HTTPException, Response

from backend.app.data.schemas import RunConfig
from backend.app.services.data_service import EpisodeNotFoundError, get_episode
from backend.app.services.export_service import load_run, new_run_id, persist_run, run_to_csv
from backend.app.services.judge_service import judge_episode
from backend.app.services.runner import run_episode

router = APIRouter()


@router.post("")
async def create_run(config: RunConfig) -> dict[str, object]:
    results = []
    for episode_id in config.episode_ids:
        try:
            episode = get_episode(episode_id)
        except EpisodeNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Episode not found: {episode_id}") from exc
        result = await run_episode(episode, config.mode, config.student_provider)
        judged = await judge_episode(episode, result, config.judge_provider)
        results.append(judged)
    run_id = new_run_id()
    payload = persist_run(run_id, config, results)
    return payload


@router.get("/{run_id}")
def read_run(run_id: str) -> dict[str, object]:
    return load_run(run_id)


@router.get("/{run_id}/events")
def read_run_events(run_id: str) -> dict[str, object]:
    payload = load_run(run_id)
    return {"run_id": run_id, "events": [{"type": "completed", "count": len(payload["results"])}]}


@router.get("/{run_id}/export.json")
def export_json(run_id: str) -> dict[str, object]:
    return load_run(run_id)


@router.get("/{run_id}/export.csv")
def export_csv(run_id: str) -> Response:
    csv_text = run_to_csv(load_run(run_id))
    return Response(content=csv_text, media_type="text/csv")
```

- [ ] **Step 5: Run export tests**

Run:

```bash
pytest backend/tests/test_exports.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/export_service.py backend/app/api/runs.py backend/tests/test_exports.py
git commit -m "feat: orchestrate runs and exports"
```

## Task 10: Next.js Frontend Scaffold and Typed API Client

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/next.config.js`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/globals.css`
- Create: `frontend/app/page.tsx`
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api.ts`
- Create: `frontend/lib/storage.ts`
- Create: `frontend/tests/workbench.test.tsx`

- [ ] **Step 1: Write frontend smoke test**

Create `frontend/tests/workbench.test.tsx`:

```tsx
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import Page from "../app/page";

test("renders the Stu-Bench workbench title", () => {
  render(<Page />);
  expect(screen.getByText("Stu-Bench Demo")).toBeInTheDocument();
  expect(screen.getByText("Student API")).toBeInTheDocument();
  expect(screen.getByText("Judge API")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend && npm test -- --run tests/workbench.test.tsx
```

Expected: FAIL because frontend project does not exist.

- [ ] **Step 3: Add frontend config**

Create `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "next dev -p 3000",
    "test": "vitest",
    "test:run": "vitest run",
    "lint": "next lint"
  },
  "dependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^15.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.5.0",
    "vitest": "^1.6.0"
  },
  "devDependencies": {
    "@playwright/test": "^1.45.0",
    "@types/node": "^20.14.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "jsdom": "^24.1.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "es2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
```

Create `frontend/next.config.js`:

```js
/** @type {import('next').NextConfig} */
const nextConfig = {};
module.exports = nextConfig;
```

Create `frontend/vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
  },
});
```

- [ ] **Step 4: Add base frontend files**

Create `frontend/app/layout.tsx`:

```tsx
import "./globals.css";

export const metadata = {
  title: "Stu-Bench Demo",
  description: "Local-first learner simulation benchmark workbench",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

Create `frontend/app/globals.css`:

```css
:root {
  --bg: #f4f6f8;
  --panel: #ffffff;
  --panel-muted: #f8fafc;
  --text: #111827;
  --muted: #5b6472;
  --border: #d8dee9;
  --accent: #1769e0;
}

[data-theme="dark"] {
  --bg: #0f172a;
  --panel: #111827;
  --panel-muted: #1f2937;
  --text: #f9fafb;
  --muted: #cbd5e1;
  --border: #374151;
  --accent: #60a5fa;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button, input, select {
  font: inherit;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

Create `frontend/app/page.tsx`:

```tsx
export default function Page() {
  return (
    <main style={{ padding: 20 }}>
      <h1>Stu-Bench Demo</h1>
      <section aria-label="Student API">Student API</section>
      <section aria-label="Judge API">Judge API</section>
    </main>
  );
}
```

Create `frontend/lib/types.ts`:

```ts
export type ProviderPreset = "openai" | "deepseek" | "qwen" | "custom" | "mock";
export type TestMode = "roleplay" | "profile" | "context_engineered";

export interface ProviderConfig {
  preset: ProviderPreset;
  base_url: string;
  api_key: string;
  model: string;
  temperature: number;
}
```

Create `frontend/lib/api.ts`:

```ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}
```

Create `frontend/lib/storage.ts`:

```ts
export function saveRememberedConfig(key: string, value: unknown, remember: boolean): void {
  if (typeof window === "undefined") return;
  if (remember) {
    window.localStorage.setItem(key, JSON.stringify(value));
  } else {
    window.localStorage.removeItem(key);
  }
}
```

- [ ] **Step 5: Run frontend test**

Run:

```bash
cd frontend && npm test -- --run tests/workbench.test.tsx
```

Expected: PASS after dependencies are installed.

- [ ] **Step 6: Commit**

```bash
git add frontend package.json
git commit -m "chore: scaffold Next.js frontend"
```

## Task 11: Workbench UI Components with Light/Dark Mode

**Files:**
- Create: `frontend/components/ApiConfigPanel.tsx`
- Create: `frontend/components/ThemeToggle.tsx`
- Create: `frontend/components/EpisodeWorkbench.tsx`
- Create: `frontend/components/DialogueTimeline.tsx`
- Create: `frontend/components/ResultsPanel.tsx`
- Create: `frontend/components/ScoreGrid.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/tests/workbench.test.tsx`

- [ ] **Step 1: Expand frontend test for workbench controls**

Replace `frontend/tests/workbench.test.tsx`:

```tsx
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import Page from "../app/page";

test("renders the three-column Stu-Bench workbench controls", () => {
  render(<Page />);
  expect(screen.getByText("Stu-Bench Demo")).toBeInTheDocument();
  expect(screen.getByLabelText("Student provider")).toBeInTheDocument();
  expect(screen.getByLabelText("Judge provider")).toBeInTheDocument();
  expect(screen.getByLabelText("Testing mode")).toBeInTheDocument();
  expect(screen.getByText("Episode")).toBeInTheDocument();
  expect(screen.getByText("Results")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Run selected" })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend && npm test -- --run tests/workbench.test.tsx
```

Expected: FAIL because components are not implemented.

- [ ] **Step 3: Implement API config panel**

Create `frontend/components/ApiConfigPanel.tsx`:

```tsx
import type { ProviderConfig } from "../lib/types";

interface Props {
  title: string;
  provider: ProviderConfig;
  onChange: (provider: ProviderConfig) => void;
  providerLabel: string;
}

const presets = ["openai", "deepseek", "qwen", "custom", "mock"] as const;

export function ApiConfigPanel({ title, provider, onChange, providerLabel }: Props) {
  return (
    <section className="panel-block" aria-label={title}>
      <h2>{title}</h2>
      <label>
        {providerLabel}
        <select
          aria-label={providerLabel}
          value={provider.preset}
          onChange={(event) => onChange({ ...provider, preset: event.target.value as ProviderConfig["preset"] })}
        >
          {presets.map((preset) => (
            <option key={preset} value={preset}>{preset}</option>
          ))}
        </select>
      </label>
      <label>
        Model
        <input value={provider.model} onChange={(event) => onChange({ ...provider, model: event.target.value })} />
      </label>
      <label>
        API key
        <input type="password" value={provider.api_key} onChange={(event) => onChange({ ...provider, api_key: event.target.value })} />
      </label>
      <label>
        Temperature
        <input
          type="number"
          min="0"
          max="2"
          step="0.1"
          value={provider.temperature}
          onChange={(event) => onChange({ ...provider, temperature: Number(event.target.value) })}
        />
      </label>
    </section>
  );
}
```

Create `frontend/components/ThemeToggle.tsx`:

```tsx
"use client";

export function ThemeToggle() {
  function toggleTheme() {
    const current = document.documentElement.dataset.theme;
    document.documentElement.dataset.theme = current === "dark" ? "light" : "dark";
  }

  return <button type="button" onClick={toggleTheme}>Toggle theme</button>;
}
```

- [ ] **Step 4: Implement workbench components**

Create `frontend/components/DialogueTimeline.tsx`:

```tsx
export function DialogueTimeline() {
  return (
    <div className="timeline" aria-label="Dialogue timeline">
      <div className="turn tutor">Tutor: Select an episode and start a run.</div>
      <div className="turn student">Student responses will appear one turn at a time.</div>
    </div>
  );
}
```

Create `frontend/components/ScoreGrid.tsx`:

```tsx
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
```

Create `frontend/components/ResultsPanel.tsx`:

```tsx
import { ScoreGrid } from "./ScoreGrid";

export function ResultsPanel() {
  return (
    <aside className="panel results-panel">
      <h2>Results</h2>
      <ScoreGrid />
      <div className="rationale">Judge rationale will appear here after a run.</div>
      <div className="button-row">
        <button type="button">Export CSV</button>
        <button type="button">Export JSON</button>
      </div>
    </aside>
  );
}
```

Create `frontend/components/EpisodeWorkbench.tsx`:

```tsx
"use client";

import { useState } from "react";

import { ApiConfigPanel } from "./ApiConfigPanel";
import { DialogueTimeline } from "./DialogueTimeline";
import { ResultsPanel } from "./ResultsPanel";
import { ThemeToggle } from "./ThemeToggle";
import type { ProviderConfig, TestMode } from "../lib/types";

const mockProvider: ProviderConfig = {
  preset: "mock",
  base_url: "mock://local",
  api_key: "mock",
  model: "mock-student",
  temperature: 0.7,
};

export function EpisodeWorkbench() {
  const [studentProvider, setStudentProvider] = useState<ProviderConfig>(mockProvider);
  const [judgeProvider, setJudgeProvider] = useState<ProviderConfig>({ ...mockProvider, model: "mock-judge" });
  const [mode, setMode] = useState<TestMode>("context_engineered");

  return (
    <main className="workbench">
      <header className="topbar">
        <div>
          <h1>Stu-Bench Demo</h1>
          <p>Local-first benchmark workbench for simulated student realism.</p>
        </div>
        <ThemeToggle />
      </header>
      <section className="columns">
        <aside className="panel setup-panel">
          <ApiConfigPanel title="Student API" providerLabel="Student provider" provider={studentProvider} onChange={setStudentProvider} />
          <ApiConfigPanel title="Judge API" providerLabel="Judge provider" provider={judgeProvider} onChange={setJudgeProvider} />
          <label>
            Testing mode
            <select aria-label="Testing mode" value={mode} onChange={(event) => setMode(event.target.value as TestMode)}>
              <option value="roleplay">Roleplay Prompt</option>
              <option value="profile">Profile Prompt</option>
              <option value="context_engineered">Context-Engineered SCS</option>
            </select>
          </label>
          <button type="button">Test connections</button>
          <button type="button">Run current</button>
          <button type="button">Run selected</button>
        </aside>
        <section className="panel episode-panel">
          <h2>Episode</h2>
          <div className="question-box">Question and answer options will load here.</div>
          <div className="context-grid">
            <div>SCS summary</div>
            <div>Scaffold sequence</div>
          </div>
          <DialogueTimeline />
        </section>
        <ResultsPanel />
      </section>
    </main>
  );
}
```

Replace `frontend/app/page.tsx`:

```tsx
import { EpisodeWorkbench } from "../components/EpisodeWorkbench";

export default function Page() {
  return <EpisodeWorkbench />;
}
```

- [ ] **Step 5: Add layout CSS**

Append to `frontend/app/globals.css`:

```css
.workbench {
  min-height: 100vh;
  padding: 18px;
}
.topbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 14px;
}
.topbar h1 {
  margin: 0;
  font-size: 28px;
}
.topbar p {
  margin: 4px 0 0;
  color: var(--muted);
}
.columns {
  display: grid;
  grid-template-columns: 300px minmax(420px, 1fr) 360px;
  gap: 14px;
  align-items: stretch;
}
.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  min-width: 0;
}
.panel-block {
  border-bottom: 1px solid var(--border);
  padding-bottom: 12px;
  margin-bottom: 12px;
}
.panel h2,
.panel-block h2 {
  font-size: 16px;
  margin: 0 0 10px;
}
label {
  display: grid;
  gap: 6px;
  color: var(--text);
  font-size: 13px;
  margin-bottom: 10px;
}
input,
select,
button {
  min-height: 36px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel-muted);
  color: var(--text);
  padding: 7px 9px;
}
button {
  cursor: pointer;
}
.setup-panel {
  display: grid;
  align-content: start;
  gap: 8px;
}
.episode-panel {
  display: grid;
  grid-template-rows: auto auto auto 1fr;
  gap: 12px;
  min-height: 620px;
}
.question-box,
.context-grid > div,
.rationale,
.turn,
.score-card {
  background: var(--panel-muted);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
}
.question-box {
  min-height: 86px;
  padding: 12px;
  overflow: auto;
}
.context-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.context-grid > div {
  min-height: 74px;
  padding: 12px;
  overflow: auto;
}
.timeline {
  min-height: 260px;
  max-height: 420px;
  overflow: auto;
  display: grid;
  align-content: start;
  gap: 10px;
}
.turn {
  padding: 10px;
}
.student {
  border-left: 4px solid var(--accent);
}
.score-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.score-card {
  min-height: 72px;
  padding: 10px;
  display: grid;
  gap: 6px;
}
.score-card span {
  color: var(--muted);
  font-size: 12px;
}
.score-card strong {
  font-size: 24px;
}
.rationale {
  margin-top: 12px;
  min-height: 150px;
  max-height: 260px;
  padding: 12px;
  overflow: auto;
}
.button-row {
  margin-top: 12px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
@media (max-width: 980px) {
  .columns {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 6: Run frontend tests**

Run:

```bash
cd frontend && npm test -- --run tests/workbench.test.tsx
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend
git commit -m "feat: add workbench UI shell"
```

## Task 12: Connect Frontend to Backend Episodes and Runs

**Files:**
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/components/EpisodeWorkbench.tsx`
- Modify: `frontend/components/DialogueTimeline.tsx`
- Modify: `frontend/components/ResultsPanel.tsx`
- Modify: `frontend/components/ScoreGrid.tsx`
- Modify: `frontend/tests/workbench.test.tsx`

- [ ] **Step 1: Write connected UI test with mocked fetch**

Replace `frontend/tests/workbench.test.tsx`:

```tsx
import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import Page from "../app/page";

beforeEach(() => {
  global.fetch = vi.fn(async (url: RequestInfo | URL) => {
    const textUrl = String(url);
    if (textUrl.endsWith("/api/episodes")) {
      return new Response(JSON.stringify({
        episodes: [{ episode_id: "demo-001", question_id: 104614, intervention_id: 10, problem_preview: "Rounding question", scaffold_turns: 1 }]
      }), { status: 200 });
    }
    if (textUrl.endsWith("/api/episodes/demo-001")) {
      return new Response(JSON.stringify({
        episode_id: "demo-001",
        problem: { text: "Rounding question", answer_options: [{ label: "A", text: "Only Alex" }] },
        lcs: { scs: { visible_learner_profile: "Year 7 learner" }, scaffold_sequence: [{ message: "Tutor hint" }] }
      }), { status: 200 });
    }
    return new Response("{}", { status: 200 });
  }) as typeof fetch;
});

test("loads episode summaries from the backend", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("Rounding question")).toBeInTheDocument());
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend && npm test -- --run tests/workbench.test.tsx
```

Expected: FAIL because UI does not fetch episodes.

- [ ] **Step 3: Extend frontend types**

Replace `frontend/lib/types.ts`:

```ts
export type ProviderPreset = "openai" | "deepseek" | "qwen" | "custom" | "mock";
export type TestMode = "roleplay" | "profile" | "context_engineered";

export interface ProviderConfig {
  preset: ProviderPreset;
  base_url: string;
  api_key: string;
  model: string;
  temperature: number;
}

export interface EpisodeSummary {
  episode_id: string;
  question_id: number;
  intervention_id: number;
  problem_preview: string;
  scaffold_turns: number;
}

export interface EpisodeDetail {
  episode_id: string;
  problem: {
    text: string;
    answer_options: Array<{ label: string; text: string }>;
  };
  lcs: {
    scs: Record<string, unknown>;
    scaffold_sequence: Array<{ message: string }>;
  };
}

export interface RunPayload {
  run_id: string;
  results: Array<{
    episode_id: string;
    status: "succeeded" | "failed";
    generated_trajectory: Array<{ turn_index: number; tutor_message: string; student_response: string }>;
    judge_scores?: Record<string, unknown>;
    error_message?: string;
  }>;
}
```

- [ ] **Step 4: Implement episode loading in workbench**

Update `frontend/components/EpisodeWorkbench.tsx` to fetch `/api/episodes`, load first episode detail, and render the preview. Keep existing layout class names.

Use this component body:

```tsx
"use client";

import { useEffect, useState } from "react";

import { ApiConfigPanel } from "./ApiConfigPanel";
import { DialogueTimeline } from "./DialogueTimeline";
import { ResultsPanel } from "./ResultsPanel";
import { ThemeToggle } from "./ThemeToggle";
import { apiGet, apiPost } from "../lib/api";
import type { EpisodeDetail, EpisodeSummary, ProviderConfig, RunPayload, TestMode } from "../lib/types";

const mockProvider: ProviderConfig = {
  preset: "mock",
  base_url: "mock://local",
  api_key: "mock",
  model: "mock-student",
  temperature: 0.7,
};

export function EpisodeWorkbench() {
  const [studentProvider, setStudentProvider] = useState<ProviderConfig>(mockProvider);
  const [judgeProvider, setJudgeProvider] = useState<ProviderConfig>({ ...mockProvider, model: "mock-judge" });
  const [mode, setMode] = useState<TestMode>("context_engineered");
  const [episodes, setEpisodes] = useState<EpisodeSummary[]>([]);
  const [selectedEpisodeId, setSelectedEpisodeId] = useState("");
  const [episode, setEpisode] = useState<EpisodeDetail | null>(null);
  const [run, setRun] = useState<RunPayload | null>(null);

  useEffect(() => {
    apiGet<{ episodes: EpisodeSummary[] }>("/api/episodes").then((payload) => {
      setEpisodes(payload.episodes);
      if (payload.episodes[0]) setSelectedEpisodeId(payload.episodes[0].episode_id);
    });
  }, []);

  useEffect(() => {
    if (!selectedEpisodeId) return;
    apiGet<EpisodeDetail>(`/api/episodes/${selectedEpisodeId}`).then(setEpisode);
  }, [selectedEpisodeId]);

  async function runSelected() {
    const payload = await apiPost<RunPayload>("/api/runs", {
      mode,
      student_provider: studentProvider,
      judge_provider: judgeProvider,
      episode_ids: selectedEpisodeId ? [selectedEpisodeId] : episodes.map((item) => item.episode_id),
    });
    setRun(payload);
  }

  return (
    <main className="workbench">
      <header className="topbar">
        <div>
          <h1>Stu-Bench Demo</h1>
          <p>Local-first benchmark workbench for simulated student realism.</p>
        </div>
        <ThemeToggle />
      </header>
      <section className="columns">
        <aside className="panel setup-panel">
          <ApiConfigPanel title="Student API" providerLabel="Student provider" provider={studentProvider} onChange={setStudentProvider} />
          <ApiConfigPanel title="Judge API" providerLabel="Judge provider" provider={judgeProvider} onChange={setJudgeProvider} />
          <label>
            Testing mode
            <select aria-label="Testing mode" value={mode} onChange={(event) => setMode(event.target.value as TestMode)}>
              <option value="roleplay">Roleplay Prompt</option>
              <option value="profile">Profile Prompt</option>
              <option value="context_engineered">Context-Engineered SCS</option>
            </select>
          </label>
          <label>
            Episode
            <select value={selectedEpisodeId} onChange={(event) => setSelectedEpisodeId(event.target.value)}>
              {episodes.map((item) => (
                <option key={item.episode_id} value={item.episode_id}>{item.episode_id}</option>
              ))}
            </select>
          </label>
          <button type="button">Test connections</button>
          <button type="button" onClick={runSelected}>Run selected</button>
        </aside>
        <section className="panel episode-panel">
          <h2>Episode</h2>
          <div className="question-box">
            {episode ? (
              <>
                <strong>{episode.problem.text}</strong>
                <ul>{episode.problem.answer_options.map((option) => <li key={option.label}>{option.label}. {option.text}</li>)}</ul>
              </>
            ) : "Loading episode..."}
          </div>
          <div className="context-grid">
            <div>{episode ? JSON.stringify(episode.lcs.scs, null, 2) : "SCS summary"}</div>
            <div>{episode ? episode.lcs.scaffold_sequence.map((turn) => turn.message).join("\n") : "Scaffold sequence"}</div>
          </div>
          <DialogueTimeline turns={run?.results[0]?.generated_trajectory ?? []} />
        </section>
        <ResultsPanel run={run} />
      </section>
    </main>
  );
}
```

- [ ] **Step 5: Update timeline/results components**

Replace `frontend/components/DialogueTimeline.tsx`:

```tsx
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
```

Replace `frontend/components/ResultsPanel.tsx`:

```tsx
import type { RunPayload } from "../lib/types";
import { ScoreGrid } from "./ScoreGrid";

export function ResultsPanel({ run }: { run: RunPayload | null }) {
  const scores = run?.results[0]?.judge_scores ?? null;
  return (
    <aside className="panel results-panel">
      <h2>Results</h2>
      <ScoreGrid scores={scores} />
      <div className="rationale">{String(scores?.judge_rationale ?? "Judge rationale will appear here after a run.")}</div>
      <div className="button-row">
        <button type="button">Export CSV</button>
        <button type="button">Export JSON</button>
      </div>
    </aside>
  );
}
```

Replace `frontend/components/ScoreGrid.tsx`:

```tsx
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
```

- [ ] **Step 6: Run frontend tests**

Run:

```bash
cd frontend && npm test -- --run tests/workbench.test.tsx
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend
git commit -m "feat: connect workbench to backend"
```

## Task 13: Visual QA for Contrast, Overflow, and Responsive Layout

**Files:**
- Create: `frontend/tests/visual.spec.ts`
- Modify: `frontend/package.json`

- [ ] **Step 1: Add visual QA test**

Create `frontend/tests/visual.spec.ts`:

```ts
import { test, expect } from "@playwright/test";

test("workbench renders without obvious overlap on desktop and mobile", async ({ page }) => {
  await page.goto("http://localhost:3000");
  await expect(page.getByText("Stu-Bench Demo")).toBeVisible();
  await page.setViewportSize({ width: 1280, height: 800 });
  await expect(page.locator(".columns")).toBeVisible();
  await expect(page).toHaveScreenshot("workbench-desktop-light.png", { fullPage: true });
  await page.getByRole("button", { name: "Toggle theme" }).click();
  await expect(page).toHaveScreenshot("workbench-desktop-dark.png", { fullPage: true });
  await page.setViewportSize({ width: 390, height: 900 });
  await expect(page.locator(".columns")).toBeVisible();
  await expect(page).toHaveScreenshot("workbench-mobile-dark.png", { fullPage: true });
});
```

- [ ] **Step 2: Add Playwright script**

Modify `frontend/package.json` scripts to include:

```json
"visual": "playwright test tests/visual.spec.ts"
```

- [ ] **Step 3: Run app and visual test**

Run backend:

```bash
npm run backend:dev
```

Run frontend:

```bash
npm run frontend:dev
```

Run visual QA:

```bash
cd frontend && npm run visual
```

Expected: screenshots are generated and test passes. If screenshots fail due to baseline creation, review the generated images and commit accepted snapshots only after confirming no overlap, no low contrast, and no text overflow.

- [ ] **Step 4: Commit**

```bash
git add frontend
git commit -m "test: add visual QA coverage"
```

## Task 14: End-to-End Mock Run and Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/demo-runbook.md`

- [ ] **Step 1: Write runbook**

Create `docs/demo-runbook.md`:

````markdown
# Stu-Bench Demo Runbook

## Local Mock Run

1. Install backend dependencies:

```bash
pip install -e ".[dev]"
```

2. Install frontend dependencies:

```bash
cd frontend && npm install
```

3. Start backend:

```bash
npm run backend:dev
```

4. Start frontend:

```bash
npm run frontend:dev
```

5. Open `http://localhost:3000`.

6. Use `mock` for both Student API and Judge API.

7. Select `Context-Engineered SCS`.

8. Click `Run selected`.

9. Confirm the dialogue timeline, score cards, judge rationale, and exports populate.

## Real Provider Connection Test

Use OpenAI, DeepSeek, Qwen, or Custom provider with base URL, model, API key, and temperature. The connection test sends a minimal request before running an episode.

## Research Notes

The app simulates each episode turn by turn. It resets conversation history between episodes. SCS is never allowed to contain ground-truth answer, full real trajectory, or judge rubric.
````

- [ ] **Step 2: Update README**

Append to `README.md`:

```markdown
## Demo Runbook

See [docs/demo-runbook.md](docs/demo-runbook.md) for mock runs, real provider connection tests, and research protocol notes.
```

- [ ] **Step 3: Run full verification**

Run:

```bash
npm run backend:test
cd frontend && npm test -- --run
```

Expected: backend and frontend tests pass.

- [ ] **Step 4: Start dev servers and manually verify mock run**

Run:

```bash
npm run backend:dev
npm run frontend:dev
```

Open `http://localhost:3000`, run one mock episode, and verify:

- One student response appears per scaffold turn.
- Results panel shows 0-100 scores.
- No previous episode history appears when running another episode.
- Light and dark modes remain readable.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/demo-runbook.md
git commit -m "docs: add Stu-Bench demo runbook"
```

## Final Verification

Run:

```bash
git status --short
npm run backend:test
cd frontend && npm test -- --run
```

Expected:

- `git status --short` shows no uncommitted changes except intentionally ignored local run artifacts.
- Backend tests pass.
- Frontend tests pass.

Then run:

```bash
git log --oneline --decorate -5
```

Expected: recent commits correspond to the tasks above.

## Plan Self-Review Notes

Spec coverage:

- Local-first Next.js + FastAPI architecture: Tasks 1, 10, 11, 12.
- 20 prepared Eedi LCS records: Tasks 2, 3, 4.
- LCS/SCS/ECS as structured context engineering: Tasks 2, 3, 4, 5.
- Three modes: Task 5 and Task 12.
- OpenAI-compatible provider presets and connection tests: Task 6 and Task 12.
- Turn-by-turn simulation and memory reset: Task 7.
- LLM-as-judge and 0-100 diagnostic scores: Task 8.
- CSV/JSON export: Task 9.
- Light/dark mode and no visual overlap: Tasks 11 and 13.
- Mock run without API cost and real provider readiness: Tasks 6, 9, 14.

Known implementation choice:

- The first preparation script uses deterministic heuristic LCS fields and marks ground truth answer as `pending_annotation` until richer annotation is available. This is intentional for v1 demo stability and is represented by metric status fields rather than presented as human-verified annotation.
