import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

# SQLite database file in the project root for simplicity
DB_PATH = BASE_DIR / "data" / "app.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Grok-related settings (stubbed for now, but wired for future use)
GROK_API_BASE_URL = os.getenv("GROK_API_BASE_URL", "https://api.grok.example.com")
GROK_API_KEY = os.getenv("GROK_API_KEY", "")

# Path to the local sample posts file used by the refresh pipeline
SAMPLE_POSTS_PATH = BASE_DIR / "data" / "sample_posts.json"

