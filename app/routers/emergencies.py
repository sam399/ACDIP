from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import DamageReport, EmergencyRequest, PriorityOverride
from app.models.common import utc_now
from app.services.priority import rerank_pending_requests, run_ai_triage
from app.services.vulnerability import AI_PRIORITY_SCORES, apply_vulnerability_scores, hvi_score_for
from app.web import save_upload, templates


router = APIRouter()


@router.get("/sos", response_class=HTMLResponse)
async def get_sos_page(request: Request, db: AsyncSession = Depends(get_db)):
    request_ids = [
        int(value)
        for value in request.cookies.get("my_requests", "").split(",")
        if value.strip().isdigit()
    ]
    my_requests = []
    if request_ids:
        result = await db.execute(
            select(EmergencyRequest)
            .options(selectinload(EmergencyRequest.vulnerability_assessment))
            .where(EmergencyRequest.id.in_(request_ids))
            .order_by(EmergencyRequest.created_at.desc())
        )
        my_requests = list(result.scalars().all())
        for emergency in my_requests:
            emergency.display_hvi_score = hvi_score_for(emergency)
    return templates.TemplateResponse(
        request=request,
        name="sos.html",
        context={"my_requests": my_requests, "current_tab": "sos"},
    )


@router.post("/sos/submit", response_class=RedirectResponse)
async def submit_sos_request(
    request: Request,
    background_tasks: BackgroundTasks,
    full_name: str = Form(...),
    phone_number: str = Form(...),
    location: str = Form(...),
    people_affected: int = Form(...),
    elderly_members: int = Form(0),
    children: int = Form(0),
    pregnant_women: int = Form(0),
    members_with_disabilities: int = Form(0),
    members_with_chronic_illness: int = Form(0),
    request_type: str = Form(...),
    description: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    photo: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    composition = (
        elderly_members,
        children,
        pregnant_women,
        members_with_disabilities,
        members_with_chronic_illness,
    )
    if people_affected < 1 or any(value < 0 for value in composition):
        return HTMLResponse(
            "Household counts must be non-negative and household size must be at least 1.",
            status_code=422,
        )

    description = description or f"Emergency request for {request_type.lower()} support."
    emergency = EmergencyRequest(
        title=f"{request_type}: {description[:30]}...",
        description=description,
        priority="Medium",
        location=location,
        latitude=latitude,
        longitude=longitude,
        status="Pending",
        people_affected=people_affected,
        elderly_members=elderly_members,
        children=children,
        pregnant_women=pregnant_women,
        members_with_disabilities=members_with_disabilities,
        members_with_chronic_illness=members_with_chronic_illness,
        request_type=request_type,
        contact_name=full_name,
        contact_phone=phone_number,
        photo_url=save_upload(photo),
        created_at=utc_now(),
    )
    apply_vulnerability_scores(emergency, "Medium")
    db.add(emergency)
    await db.flush()
    from app.services.trust import evaluate_trust_score
    import json
    trust_res = await evaluate_trust_score(emergency, db, is_emergency=True)
    emergency.trust_score = trust_res["score"]
    emergency.trust_breakdown = json.dumps(trust_res["breakdown"])
    existing_cookie = request.cookies.get("my_requests", "")
    updated_cookie = f"{existing_cookie},{emergency.id}" if existing_cookie else str(emergency.id)
    await db.commit()
    background_tasks.add_task(run_ai_triage, emergency.id)

    response = RedirectResponse(url="/sos", status_code=303)
    response.set_cookie("my_requests", updated_cookie, max_age=60 * 60 * 24 * 30)
    return response


@router.post("/admin/requests/{request_id}/priority-override", response_class=RedirectResponse)
async def override_request_priority(
    request_id: int,
    priority: str = Form(...),
    justification: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if priority not in AI_PRIORITY_SCORES or not justification.strip():
        return HTMLResponse("A valid priority and justification are required.", status_code=422)
    emergency = await db.get(EmergencyRequest, request_id)
    if not emergency:
        return HTMLResponse("Emergency request not found.", status_code=404)
    previous_priority = emergency.priority
    emergency.priority_override = priority
    emergency.priority = priority
    emergency.override_justification = justification.strip()
    emergency.override_updated_at = utc_now()
    emergency.override_history.append(PriorityOverride(
        previous_priority=previous_priority,
        new_priority=priority,
        justification=justification.strip(),
        created_at=emergency.override_updated_at,
    ))
    await rerank_pending_requests(db)
    await db.commit()
    return RedirectResponse(url="/#priority-queue", status_code=303)


@router.post("/sos/damage", response_class=RedirectResponse)
async def submit_damage_report(
    damage_type: str = Form(...),
    location: str = Form(...),
    description: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    photo: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    damage = DamageReport(
        damage_type=damage_type,
        location=location,
        latitude=latitude,
        longitude=longitude,
        description=description or f"Reported {damage_type.lower()} infrastructure damage.",
        status="Reported",
        photo_url=save_upload(photo, "dmg_"),
        created_at=utc_now(),
    )
    db.add(damage)
    await db.flush()
    from app.services.trust import evaluate_trust_score
    import json
    trust_res = await evaluate_trust_score(damage, db, is_emergency=False)
    damage.trust_score = trust_res["score"]
    damage.trust_breakdown = json.dumps(trust_res["breakdown"])
    await db.commit()
    return RedirectResponse(url="/sos", status_code=303)


@router.get("/api/hazards")
async def get_hazards(db: AsyncSession = Depends(get_db)):
    reports = (await db.execute(
        select(DamageReport).where(DamageReport.status != "Resolved")
    )).scalars().all()
    return {
        "hazards": [
            {
                "id": report.id,
                "type": report.damage_type,
                "location": report.location,
                "latitude": report.latitude,
                "longitude": report.longitude,
                "description": report.description,
                "status": report.status,
            }
            for report in reports
            if report.latitude is not None and report.longitude is not None
        ]
    }
