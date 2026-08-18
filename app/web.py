"""Shared web paths, templates, and upload handling."""

import os
import shutil
from pathlib import Path
from time import time_ns

from fastapi import UploadFile, Request
from fastapi.templating import Jinja2Templates


class LocalizedTemplates(Jinja2Templates):
    def TemplateResponse(self, *args, **kwargs):
        # Retrieve context dictionary
        # args[0] = name (legacy starlette) or request, args[1] = context (legacy starlette) or name
        context = {}
        request = None
        
        # Check if first arg is Request (modern starlette signature)
        if len(args) > 0 and isinstance(args[0], Request):
            request = args[0]
            if len(args) >= 3:
                context = args[2]
            else:
                context = kwargs.get("context", {})
        else:
            # Fallback legacy signature mapping
            request = kwargs.get("request") or (args[0] if len(args) > 0 and not isinstance(args[0], str) else None)
            context = kwargs.get("context") or (args[1] if len(args) > 1 and isinstance(args[1], dict) else {})
            
        lang = "en"
        dark_mode = "false"
        refresh_interval = "0"
        user_role = "admin"
        if request:
            lang = request.cookies.get("lang", "en")
            dark_mode = request.cookies.get("dark_mode", "false")
            refresh_interval = request.cookies.get("refresh_interval", "0")
            user_role = request.cookies.get("user_role", "admin")
            
        from app.services.translation import get_translation_func
        context["_"] = get_translation_func(lang)
        context["lang"] = lang
        context["dark_mode"] = dark_mode
        context["refresh_interval"] = refresh_interval
        context["user_role"] = user_role
        
        # Write back updated context
        if len(args) >= 3 and isinstance(args[0], Request):
            args = list(args)
            args[2] = context
            args = tuple(args)
        elif len(args) > 1 and isinstance(args[1], dict):
            args = list(args)
            args[1] = context
            args = tuple(args)
        else:
            kwargs["context"] = context
            
        return super().TemplateResponse(*args, **kwargs)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
TEMPLATE_DIR = APP_DIR / "templates"
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(STATIC_DIR / "uploads")))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
templates = LocalizedTemplates(directory=str(TEMPLATE_DIR))


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
