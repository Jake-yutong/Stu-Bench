import json
import re
from typing import Any

from backend.app.data.schemas import FormulaMetrics, JudgeScores, MetricStatus


SCORE_FIELDS = (
    "overall_realism",
    "initial_state_fidelity",
    "mistake_authenticity",
    "scaffolding_uptake",
    "kc_transition_consistency",
    "learning_trajectory_plausibility",
    "over_competence_control",
)

FIELD_ALIASES = {
    "overall": "overall_realism",
    "overallscore": "overall_realism",
    "overallrealism": "overall_realism",
    "learnerrealism": "overall_realism",
    "learnerrealismrewardscore": "overall_realism",
    "realism": "overall_realism",
    "rewardscore": "overall_realism",
    "initial": "initial_state_fidelity",
    "initialstate": "initial_state_fidelity",
    "initiallearnerstate": "initial_state_fidelity",
    "initiallearnerstatefidelity": "initial_state_fidelity",
    "initialstatefidelity": "initial_state_fidelity",
    "mistake": "mistake_authenticity",
    "mistakeauth": "mistake_authenticity",
    "mistakeauthenticity": "mistake_authenticity",
    "uptake": "scaffolding_uptake",
    "scaffolduptake": "scaffolding_uptake",
    "scaffoldinguptake": "scaffolding_uptake",
    "scaffoldinguptakescore": "scaffolding_uptake",
    "scaffoldadherence": "scaffolding_uptake",
    "scaffoldresponsiveness": "scaffolding_uptake",
    "uptakeevidence": "scaffolding_uptake",
    "uptakerealism": "scaffolding_uptake",
    "uptakerelevance": "scaffolding_uptake",
    "kctransition": "kc_transition_consistency",
    "kctransitionconsistency": "kc_transition_consistency",
    "kctransitionsimilarity": "kc_transition_consistency",
    "kts": "kc_transition_consistency",
    "trajectory": "learning_trajectory_plausibility",
    "learningtrajectory": "learning_trajectory_plausibility",
    "learningtrajectoryplausibility": "learning_trajectory_plausibility",
    "trajectoryrealism": "learning_trajectory_plausibility",
    "overcompetence": "over_competence_control",
    "overcompetencecontrol": "over_competence_control",
    "overimprovementcontrol": "over_competence_control",
}

FORMULA_ALIASES = {
    "kts": "kts",
    "kctransitionsimilarity": "kts",
    "kctransition": "kts",
    "uptake": "uptake",
    "uptakerate": "uptake",
    "scaffoldinguptake": "uptake",
    "scaffoldinguptakerate": "uptake",
    "overimprove": "over_improve",
    "overimprovement": "over_improve",
    "overimprovementrate": "over_improve",
    "overcompetence": "over_improve",
}

TOP_LEVEL_FORMULA_KEYS = {
    "kts",
    "uptake",
    "overimprove",
    "overimprovement",
    "overimprovementrate",
    "metricstatus",
}


def load_judge_payload(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = json.loads(_extract_json_object(text))
    if not isinstance(data, dict):
        raise ValueError("Judge payload must be a JSON object")
    return data


def normalize_judge_scores(payload: dict[str, Any]) -> JudgeScores:
    score_source = _merge_score_sources(payload)
    formula = _normalize_formula_metrics(payload)
    scores: dict[str, int] = {}
    flags = _string_list(payload.get("failure_flags") or payload.get("flags"))

    for key, value in score_source.items():
        field = _canonical_score_field(key)
        if field and value is not None and field not in scores:
            scores[field] = _coerce_score(value)

    if formula.uptake is not None and "scaffolding_uptake" not in scores:
        scores["scaffolding_uptake"] = _ratio_to_score(formula.uptake)
        flags.append("scaffolding_uptake_derived_from_formula")
    if formula.kts is not None and "kc_transition_consistency" not in scores:
        scores["kc_transition_consistency"] = _ratio_to_score(formula.kts)
        flags.append("kc_transition_consistency_derived_from_formula")
    if formula.over_improve is not None and "over_competence_control" not in scores:
        scores["over_competence_control"] = _ratio_to_score(1 - formula.over_improve)
        flags.append("over_competence_control_derived_from_formula")

    if "overall_realism" not in scores:
        diagnostic_values = [scores[field] for field in SCORE_FIELDS[1:] if field in scores]
        if diagnostic_values:
            scores["overall_realism"] = round(sum(diagnostic_values) / len(diagnostic_values))
            flags.append("overall_realism_derived_from_diagnostics")

    fallback = scores.get("overall_realism")
    for field in SCORE_FIELDS:
        if field not in scores:
            scores[field] = fallback if fallback is not None else 50
            flags.append(f"{field}_filled_from_fallback")

    rationale = _first_string(
        payload,
        ("judge_rationale", "rationale", "reasoning", "explanation", "comment"),
    )
    if not rationale:
        rationale = "Judge returned scores without a rationale."
        flags.append("missing_judge_rationale")

    return JudgeScores(
        **scores,
        judge_rationale=rationale,
        failure_flags=flags,
        formula_metrics=formula,
    )


def _extract_json_object(text: str) -> str:
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fence_match:
        return fence_match.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("No JSON object found", text, 0)
    return text[start : end + 1]


def _merge_score_sources(payload: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for nested_key in ("scores", "score", "diagnostic_scores", "metrics", "judge_scores"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            merged.update(nested)
    merged.update(payload)
    return merged


def _normalize_formula_metrics(payload: dict[str, Any]) -> FormulaMetrics:
    source: dict[str, Any] = {}
    for nested_key in ("formula_metrics", "computed_metrics", "process_metrics", "metrics"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            source.update(nested)
    source.update(
        {
            key: value
            for key, value in payload.items()
            if _normalize_key(key) in TOP_LEVEL_FORMULA_KEYS
        }
    )

    formula_values: dict[str, float | None] = {"kts": None, "uptake": None, "over_improve": None}
    for key, value in source.items():
        field = _canonical_formula_field(key)
        if field and value is not None and formula_values[field] is None:
            formula_values[field] = _coerce_ratio(value)

    status_value = source.get("status") or source.get("metric_status")
    try:
        status = MetricStatus(status_value)
    except ValueError:
        status = MetricStatus.judge_estimated
    return FormulaMetrics(**formula_values, status=status)


def _canonical_score_field(key: str) -> str | None:
    normalized = _normalize_key(key)
    if normalized in {_normalize_key(field) for field in SCORE_FIELDS}:
        return next(field for field in SCORE_FIELDS if _normalize_key(field) == normalized)
    return FIELD_ALIASES.get(normalized)


def _canonical_formula_field(key: str) -> str | None:
    return FORMULA_ALIASES.get(_normalize_key(key))


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _coerce_score(value: Any) -> int:
    number = _coerce_number(value)
    if 0 <= number <= 1:
        number *= 100
    return round(max(0, min(100, number)))


def _coerce_ratio(value: Any) -> float:
    number = _coerce_number(value)
    if number > 1:
        number /= 100
    return max(0.0, min(1.0, number))


def _ratio_to_score(value: float) -> int:
    return round(max(0, min(100, value * 100)))


def _coerce_number(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if match:
            return float(match.group(0))
    raise ValueError(f"Cannot coerce score value {value!r}")


def _first_string(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for nested_key in ("scores", "diagnostic_scores", "metrics", "judge_scores"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            nested_value = _first_string(nested, keys)
            if nested_value:
                return nested_value
    return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
