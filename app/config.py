"""
Configuration settings for AI Content Detector.
All values are loaded from environment variables with sensible defaults.
Zero required variables; works out of the box.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()

# Paths
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data")).resolve()
UPLOADS_DIR: Path = DATA_DIR / "uploads"
DATABASE_PATH: Path = DATA_DIR / "analyses.db"
STATIC_DIR: Path = BASE_DIR / "static"
CUSTOM_MODELS_DIR: Path = BASE_DIR / "custom_models"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CUSTOM_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Detection Neural Subsystems
AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "VeritasDoc-Core-Alpha")
FALLBACK_MODEL_NAME: str = os.getenv("FALLBACK_MODEL_NAME", "VeritasDoc-Core-Gamma")

# Upload limits
MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "20"))
MAX_UPLOAD_BYTES: int = MAX_UPLOAD_MB * 1024 * 1024

# Supported formats
ALLOWED_EXTENSIONS: set[str] = {".txt", ".docx", ".pdf", ".rtf", ".pptx", ".ppt", ".doc"}

# Text thresholds
MIN_DOCUMENT_WORDS: int = 50
MIN_SENTENCE_WORDS: int = 6
