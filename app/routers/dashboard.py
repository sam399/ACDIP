from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Disaster, PersonnelStatus, SupplyInventory
from app.services.priority import rerank_pending_requests
from app.services.vulnerability import final_priority_score_for, hvi_score_for, readable_breakdown
from app.services.predictive import calculate_predictive_shortages
from app.web import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        ai_weight = float(request.cookies.get("ai_weight", "60")) / 100.0
        hvi_weight = float(request.cookies.get("hvi_weight", "40")) / 100.0
    except ValueError:
        ai_weight = 0.60
        hvi_weight = 0.40

    disasters = list((await db.execute(
        select(Disaster).where(Disaster.status == "Active")
    )).scalars().all())
    priority_queue = await rerank_pending_requests(db, ai_weight, hvi_weight)
    for emergency in priority_queue:
        emergency.hvi_factor_labels = readable_breakdown(emergency)
        emergency.display_hvi_score = hvi_score_for(emergency)
        emergency.display_final_priority_score = final_priority_score_for(emergency)
    await db.commit()

    # Calculate shortages
    predictive_alerts = await calculate_predictive_shortages(db)

    supplies = list((await db.execute(select(SupplyInventory))).scalars().all())
    personnel = list((await db.execute(select(PersonnelStatus))).scalars().all())
    districts = {
        district.strip()
        for disaster in disasters
        for district in (disaster.affected_districts or "").split(",")
        if district.strip()
    }
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "disasters": disasters,
            "priority_queue": priority_queue,
            "supplies": supplies,
            "personnel": personnel,
            "active_events_count": len(disasters),
            "affected_districts_count": len(districts) if districts else 30,
            "total_requests_count": len(priority_queue),
            "predictive_alerts": predictive_alerts,
            "current_tab": "dashboard",
        },
    )

@router.get("/change-lang/{lang}", response_class=RedirectResponse)
async def change_language(lang: str, request: Request):
    referer = request.headers.get("referer", "/")
    target_lang = "bn" if lang == "bn" else "en"
    response = RedirectResponse(url=referer, status_code=303)
    response.set_cookie("lang", target_lang, max_age=60 * 60 * 24 * 365) # 1 year
    return response
