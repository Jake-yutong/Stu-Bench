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
