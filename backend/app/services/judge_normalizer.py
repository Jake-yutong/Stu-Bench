import json
import re
from typing import Any

from backend.app.data.schemas import FormulaMetrics, JudgeScores, MetricStatus


SCORE_FIELDS = (
    "lrs",
    "isf",
    "ma",
    "su",
    "ktc",
    "occ",
)

FIELD_ALIASES = {
    "overall": "lrs",
    "overallscore": "lrs",
    "overallrealism": "lrs",
    "overallrealismrewardscore": "lrs",
    "learnerrealism": "lrs",
    "learnerrealismrewardscore": "lrs",
    "learnerrealismscore": "lrs",
    "lrs": "lrs",
    "realism": "lrs",
    "rewardscore": "lrs",
    "initial": "isf",
    "initialstate": "isf",
    "initiallearnerstate": "isf",
    "initiallearnerstatefidelity": "isf",
    "initialstatefidelity": "isf",
    "isf": "isf",
    "mistake": "ma",
    "mistakeauth": "ma",
    "mistakeauthenticity": "ma",
    "ma": "ma",
    "uptake": "su",
    "scaffolduptake": "su",
    "scaffoldinguptake": "su",
    "scaffoldinguptakescore": "su",
    "scaffoldadherence": "su",
    "scaffoldresponsiveness": "su",
    "su": "su",
    "uptakeevidence": "su",
    "uptakerealism": "su",
    "uptakerelevance": "su",
    "kctransition": "ktc",
    "kctransitionconsistency": "ktc",
    "kctransitionsimilarity": "ktc",
    "ktc": "ktc",
    "kts": "ktc",
    "occ": "occ",
    "overcompetence": "occ",
    "overcompetencecontrol": "occ",
    "overimprovementcontrol": "occ",
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
    scores: dict[str, float] = {}
    flags = _string_list(payload.get("failure_flags") or payload.get("flags"))

    for key, value in score_source.items():
        field = _canonical_score_field(key)
        if field and value is not None and field not in scores:
            scores[field] = _coerce_ratio(value)

    if formula.uptake is not None and "su" not in scores:
        scores["su"] = formula.uptake
        flags.append("su_derived_from_uptake")
    if formula.kts is not None and "ktc" not in scores:
        scores["ktc"] = formula.kts
        flags.append("ktc_derived_from_kts")
    if formula.over_improve is not None and "occ" not in scores:
        scores["occ"] = 1 - formula.over_improve
        flags.append("occ_derived_from_over_improve")

    if "lrs" not in scores:
        diagnostic_values = [scores[field] for field in SCORE_FIELDS[1:] if field in scores]
        if diagnostic_values:
            scores["lrs"] = round(sum(diagnostic_values) / len(diagnostic_values), 3)
            flags.append("lrs_derived_from_diagnostics")

    fallback = scores.get("lrs")
    for field in SCORE_FIELDS:
        if field not in scores:
            scores[field] = fallback if fallback is not None else 0.5
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
    except (TypeError, ValueError):
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


def _coerce_ratio(value: Any) -> float:
    number = _coerce_number(value)
    if number > 1:
        number /= 100
    return round(max(0.0, min(1.0, number)), 3)


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
