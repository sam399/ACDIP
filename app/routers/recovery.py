from datetime import date

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Disaster, RecoveryBaseline, RecoveryMilestone
from app.models.common import utc_now
from app.services.recovery import RECOVERY_CATEGORIES, recovery_summary, weekly_trend
from app.web import save_upload, templates


router = APIRouter()


@router.get("/recovery", response_class=HTMLResponse)
async def recovery_dashboard(
    request: Request,
    disaster_id: str | None = None,
    district: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    disaster_id = disaster_id.strip() if disaster_id else ""
    if disaster_id and not disaster_id.isdigit():
        return HTMLResponse("Disaster filter must be a valid event ID.", status_code=422)
    selected_disaster_id = int(disaster_id) if disaster_id else None

    baseline_query = select(RecoveryBaseline).options(selectinload(RecoveryBaseline.disaster))
    milestone_query = select(RecoveryMilestone).options(selectinload(RecoveryMilestone.disaster))
    if selected_disaster_id:
        baseline_query = baseline_query.where(RecoveryBaseline.disaster_id == selected_disaster_id)
        milestone_query = milestone_query.where(RecoveryMilestone.disaster_id == selected_disaster_id)
    if district:
        baseline_query = baseline_query.where(RecoveryBaseline.district == district)
        milestone_query = milestone_query.where(RecoveryMilestone.district == district)
    if category in RECOVERY_CATEGORIES:
        baseline_query = baseline_query.where(RecoveryBaseline.category == category)
        milestone_query = milestone_query.where(RecoveryMilestone.category == category)

    baselines = list((await db.execute(baseline_query)).scalars().all())
    milestones = list((await db.execute(
        milestone_query.order_by(RecoveryMilestone.milestone_date.desc(), RecoveryMilestone.id.desc())
    )).scalars().all())
    disasters = list((await db.execute(select(Disaster).order_by(Disaster.created_at.desc()))).scalars().all())
    district_values = list((await db.execute(
        select(RecoveryBaseline.district).distinct().order_by(RecoveryBaseline.district)
    )).scalars().all())

    return templates.TemplateResponse(
        request=request,
        name="recovery.html",
        context={
            "current_tab": "recovery",
            "disasters": disasters,
            "districts": district_values,
            "categories": RECOVERY_CATEGORIES,
            "summary": recovery_summary(baselines, milestones),
            "milestones": milestones,
            "trend": weekly_trend(milestones),
            "filters": {
                "disaster_id": selected_disaster_id,
                "district": district,
                "category": category,
            },
        },
    )


@router.post("/admin/recovery/baselines", response_class=RedirectResponse)
async def set_recovery_baseline(
    disaster_id: int = Form(...),
    district: str = Form(...),
    category: str = Form(...),
    estimated_total: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    district = district.strip()
    if category not in RECOVERY_CATEGORIES or estimated_total < 1 or not district:
        return HTMLResponse("A valid district, category, and positive baseline total are required.", status_code=422)
    if not await db.get(Disaster, disaster_id):
        return HTMLResponse("Disaster event not found.", status_code=404)
    baseline = (await db.execute(select(RecoveryBaseline).where(
        RecoveryBaseline.disaster_id == disaster_id,
        RecoveryBaseline.district == district,
        RecoveryBaseline.category == category,
    ))).scalar_one_or_none()
    if baseline:
        baseline.estimated_total = estimated_total
        baseline.updated_at = utc_now()
    else:
        db.add(RecoveryBaseline(
            disaster_id=disaster_id, district=district, category=category,
            estimated_total=estimated_total,
        ))
    await db.commit()
    return RedirectResponse(url="/recovery", status_code=303)


@router.post("/admin/recovery/milestones", response_class=RedirectResponse)
async def add_recovery_milestone(
    disaster_id: int = Form(...),
    district: str = Form(...),
    category: str = Form(...),
    completed_count: int = Form(...),
    milestone_date: date = Form(...),
    affected_area: str = Form(...),
    verification_notes: str | None = Form(None),
    evidence_photo: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    district, affected_area = district.strip(), affected_area.strip()
    if category not in RECOVERY_CATEGORIES or completed_count < 1 or not district or not affected_area:
        return HTMLResponse("Valid milestone details and a positive completed count are required.", status_code=422)
    if milestone_date > date.today():
        return HTMLResponse("Milestone date cannot be in the future.", status_code=422)
    if not await db.get(Disaster, disaster_id):
        return HTMLResponse("Disaster event not found.", status_code=404)
    baseline = (await db.execute(select(RecoveryBaseline).where(
        RecoveryBaseline.disaster_id == disaster_id,
        RecoveryBaseline.district == district,
        RecoveryBaseline.category == category,
    ))).scalar_one_or_none()
    if not baseline:
        return HTMLResponse("Create the matching recovery baseline before recording a milestone.", status_code=422)
    db.add(RecoveryMilestone(
        disaster_id=disaster_id, district=district, category=category,
        completed_count=completed_count, milestone_date=milestone_date,
        affected_area=affected_area, verification_notes=(verification_notes or "").strip() or None,
        evidence_photo_url=save_upload(evidence_photo, "recovery_"), is_verified=True,
    ))
    await db.commit()
    return RedirectResponse(url="/recovery", status_code=303)
