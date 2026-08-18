"""Keep pytest completely isolated from the development SQLite database."""

import asyncio
import os
import shutil
from pathlib import Path


TEST_DB = Path(__file__).resolve().parent / ".test_respond_er.db"
TEST_UPLOAD_DIR = Path(__file__).resolve().parent / ".test_uploads"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB.as_posix()}"
os.environ["UPLOAD_DIR"] = str(TEST_UPLOAD_DIR)


def pytest_sessionstart(session):
    # This file is test-only and is recreated before every suite run.
    if TEST_DB.exists():
        TEST_DB.unlink()
    if TEST_UPLOAD_DIR.exists():
        shutil.rmtree(TEST_UPLOAD_DIR)
    from alembic import command
    from alembic.config import Config
    from seed import seed
    command.upgrade(Config(str(Path(__file__).resolve().parent / "alembic.ini")), "head")
    asyncio.run(seed())


def pytest_sessionfinish(session, exitstatus):
    from app.database import engine

    asyncio.run(engine.dispose())
    if TEST_DB.exists():
        TEST_DB.unlink()
    if TEST_UPLOAD_DIR.exists():
        shutil.rmtree(TEST_UPLOAD_DIR)
