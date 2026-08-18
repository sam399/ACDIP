import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

@dataclass(frozen=True)
class Settings:
    PROJECT_ROOT: Path
    PROJECT_NAME: str
    DATABASE_URL: str
    SECRET_KEY: str
    GEMINI_API_KEY: str


settings = Settings(
    PROJECT_ROOT=PROJECT_ROOT,
    PROJECT_NAME="RESPOND-ER",
    DATABASE_URL=os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{(PROJECT_ROOT / 'respond_er.db').as_posix()}"),
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-12345"),
    GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", ""),
)
