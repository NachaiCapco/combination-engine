import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_PATH = Path(os.getenv("STORAGE_PATH", BASE_DIR / "workspace")).resolve()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "owner/TestForge")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
STORAGE_PATH.mkdir(parents=True, exist_ok=True)
