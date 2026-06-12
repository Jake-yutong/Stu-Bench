from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"
DATA_DIR = BACKEND_ROOT / "app" / "data"
RUN_STORAGE_DIR = BACKEND_ROOT / "app" / "storage" / "runs"
DEMO_EPISODES_PATH = DATA_DIR / "demo_episodes.json"
