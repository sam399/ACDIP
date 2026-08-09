import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "RESPOND-ER"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./respond_er.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-12345")

settings = Settings()
