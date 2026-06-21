from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"
DATA_DIR = BACKEND_ROOT / "app" / "data"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
RUN_STORAGE_DIR = BACKEND_ROOT / "app" / "storage" / "runs"
DEMO_EPISODES_PATH = DATA_DIR / "demo_episodes.json"
EEDI_TEST_MANIFEST_PATH = ARTIFACTS_DIR / "eedi2k_test_episode_manifest.csv"
ANNOTATION_SCHEMA_PATH = ARTIFACTS_DIR / "stu_bench_annotation_schema_v0_1.json"
