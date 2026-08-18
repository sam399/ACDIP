"""Shared web paths, templates, and upload handling."""

import os
import shutil
from pathlib import Path
from time import time_ns

from fastapi import UploadFile
from fastapi.templating import Jinja2Templates


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
TEMPLATE_DIR = APP_DIR / "templates"
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(STATIC_DIR / "uploads")))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def save_upload(upload: UploadFile | None, prefix: str = "") -> str | None:
    """Persist an optional upload under a sanitized, collision-resistant name."""
    if not upload or not upload.filename:
        return None
    safe_name = Path(upload.filename).name
    filename = f"{time_ns()}_{prefix}{safe_name}"
    destination = UPLOAD_DIR / filename
    with destination.open("wb") as output:
        shutil.copyfileobj(upload.file, output)
    return f"/static/uploads/{filename}"
