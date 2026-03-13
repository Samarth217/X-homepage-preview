import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

# SQLite database file in the project root for simplicity
DB_PATH = BASE_DIR / "data" / "app.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Grok / xAI settings
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
GROK_API_BASE_URL = os.getenv("GROK_API_BASE_URL", "https://api.x.ai/v1")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-0709")

# Path to the local sample posts file used by the refresh pipeline
SAMPLE_POSTS_PATH = BASE_DIR / "data" / "sample_posts.json"

