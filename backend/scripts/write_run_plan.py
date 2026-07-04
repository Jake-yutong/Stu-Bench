import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.core.config import DEMO_EPISODES_PATH


STUDENT_MODEL_GROUPS = [
    {
        "group": "flagship",
        "models": ["qwen3.7-max", "deepseek-v4-pro", "glm-5.2"],
    },
    {
        "group": "domain_tuned",
        "models": ["qwen-math-plus", "qwen-plus-character"],
    },
    {
        "group": "smaller_scale",
        "models": ["qwen3.6-35b-a3b", "qwen3.6-27b"],
    },
]

CONDITIONS = [
    {
        "mode": "roleplay",
        "label": "Roleplay Prompt",
        "description": "Only asks the model to play a student.",
    },
    {
        "mode": "profile",
        "label": "Static Profile Prompt",
        "description": "Provides a visible learner profile and initial state, but no full SCS.",
    },
    {
        "mode": "context_engineered",
        "label": "Full SCS",
        "description": "Provides the full student-facing context set, including KC state abstraction.",
    },
    {
        "mode": "no_kc_scs",
        "label": "No-KC SCS",
        "description": "Ablates KC state abstraction from the student-facing context set.",
    },
]


def main() -> None:
    parser_output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("backend/app/data/artifacts/stu_bench_20_episode_run_plan.json")
    episodes = json.loads(DEMO_EPISODES_PATH.read_text())
    total_episode_condition_pairs = len(episodes) * len(CONDITIONS)
    model_count = sum(len(group["models"]) for group in STUDENT_MODEL_GROUPS)
    total_model_condition_episode_pairs = total_episode_condition_pairs * sum(
        len(group["models"]) for group in STUDENT_MODEL_GROUPS
    )
    result_files = [
        f"stu_bench_{model}_20ep_4cond.json"
        for group in STUDENT_MODEL_GROUPS
        for model in group["models"]
    ]
    payload = {
        "plan_id": "stu-bench-20-episode-four-condition-per-model-v0.2",
        "source_split": "Eedi2k anchored-dialogues/test.csv",
        "episode_count": len(episodes),
        "scaffold_turn_count": sum(len(item["lcs"]["scaffold_sequence"]) for item in episodes),
        "conditions": CONDITIONS,
        "student_model_groups": STUDENT_MODEL_GROUPS,
        "judge_model": {
            "provider": "qwen",
            "model": "qwen3.6-flash",
            "role": "judge_estimated first-pass evaluator",
        },
        "metric_status": {
            "lrs": "judge_estimated",
            "isf": "judge_estimated",
            "ma": "judge_estimated",
            "su": "judge_estimated",
            "ktc": "judge_estimated",
            "occ": "judge_estimated",
            "formula_kts": "pending_annotation",
            "formula_uptake": "pending_annotation",
            "formula_over_improve": "pending_annotation",
        },
        "annotation_boundary": {
            "method": "llm_generated",
            "human_verification_status": "pending_human_verification",
            "paper_wording": "LLM-generated annotations with human verification planned or spot-checked; judge scores are first-pass estimates.",
        },
        "workload": {
            "episode_condition_pairs_per_model": total_episode_condition_pairs,
            "expected_result_files": model_count,
            "all_model_condition_episode_pairs": total_model_condition_episode_pairs,
        },
        "result_artifact_contract": {
            "unit": "one JSON file per student model",
            "results_per_file": total_episode_condition_pairs,
            "filename_pattern": "stu_bench_{student_model}_20ep_4cond.json",
            "required_dimensions": ["student_model", "episode_id", "mode"],
            "expected_files": result_files,
        },
        "episode_ids": [item["episode_id"] for item in episodes],
    }
    parser_output.parent.mkdir(parents=True, exist_ok=True)
    parser_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(parser_output)


if __name__ == "__main__":
    main()
