from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import SupportTicket
from app.config import settings

router = APIRouter()


@router.get("/settings", response_class=HTMLResponse)
async def get_settings_page(request: Request):
    # Read cookies or defaults
    ai_weight = request.cookies.get("ai_weight", "60")
    hvi_weight = request.cookies.get("hvi_weight", "40")
    gemini_key = request.cookies.get("gemini_key", settings.GEMINI_API_KEY or "")
    refresh_interval = request.cookies.get("refresh_interval", "0")
    dark_mode = request.cookies.get("dark_mode", "false")
    
    success = request.query_params.get("success", "")

    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "ai_weight": ai_weight,
            "hvi_weight": hvi_weight,
            "gemini_key": gemini_key,
            "refresh_interval": refresh_interval,
            "dark_mode": dark_mode,
            "success": success,
            "current_tab": "settings",
        },
    )


@router.post("/settings/save")
async def save_settings(
    ai_weight: int = Form(60),
    hvi_weight: int = Form(40),
    gemini_key: str = Form(""),
    refresh_interval: int = Form(0),
    dark_mode: str = Form("false"),
):
    response = RedirectResponse(url="/settings?success=1", status_code=303)
    response.set_cookie("ai_weight", str(ai_weight), max_age=60 * 60 * 24 * 365)
    response.set_cookie("hvi_weight", str(hvi_weight), max_age=60 * 60 * 24 * 365)
    response.set_cookie("gemini_key", gemini_key.strip(), max_age=60 * 60 * 24 * 365)
    response.set_cookie("refresh_interval", str(refresh_interval), max_age=60 * 60 * 24 * 365)
    response.set_cookie("dark_mode", dark_mode, max_age=60 * 60 * 24 * 365)
    return response


@router.get("/support", response_class=HTMLResponse)
async def get_support_page(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupportTicket).order_by(SupportTicket.created_at.desc()))
    tickets = list(result.scalars().all())
    success = request.query_params.get("success", "")
    
    return templates.TemplateResponse(
        request=request,
        name="support.html",
        context={
            "tickets": tickets,
            "success": success,
            "current_tab": "support",
        },
    )


@router.post("/support/submit")
async def submit_support_ticket(
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    ticket = SupportTicket(
        name=name.strip(),
        email=email.strip(),
        subject=subject.strip(),
        message=message.strip(),
        status="Open",
    )
    db.add(ticket)
    await db.commit()
    return RedirectResponse(url="/support?success=1", status_code=303)


@router.get("/audit-logs", response_class=HTMLResponse)
async def get_audit_logs_page(request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    from app.models import PriorityOverride

    result = await db.execute(
        select(PriorityOverride)
        .options(selectinload(PriorityOverride.request))
        .order_by(PriorityOverride.created_at.desc())
    )
    overrides = list(result.scalars().all())

    return templates.TemplateResponse(
        request=request,
        name="audit_logs.html",
        context={
            "overrides": overrides,
            "current_tab": "audit-logs",
        },
    )


@router.get("/change-role/{role}")
async def change_role(role: str, request: Request):
    referer = request.headers.get("referer", "/")
    response = RedirectResponse(url=referer, status_code=303)
    response.set_cookie("user_role", role, max_age=60 * 60 * 24 * 365)
    return response


@router.get("/reset-session")
async def reset_session():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("lang")
    response.delete_cookie("dark_mode")
    response.delete_cookie("refresh_interval")
    response.delete_cookie("ai_weight")
    response.delete_cookie("hvi_weight")
    response.delete_cookie("gemini_key")
    response.delete_cookie("user_role")
    return response


# Import templates in-module to avoid circular import issues
from app.web import templates
