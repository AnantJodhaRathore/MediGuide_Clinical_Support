from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT_DIR / "dataset"
DATA_DIR = Path(os.getenv("MEDICAL_DATA_DIR", ROOT_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = Path(os.getenv("MEDICAL_DATABASE_PATH", DATA_DIR / "medical_expert.db"))
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
FRONTEND_API_URL = os.getenv("MEDICAL_API_URL", "http://127.0.0.1:8000")
APP_NAME = "MediGuide Clinical Support"
APP_VERSION = "2.0.0"
