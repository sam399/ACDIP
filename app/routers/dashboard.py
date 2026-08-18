from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Disaster, PersonnelStatus, SupplyInventory
from app.services.priority import rerank_pending_requests
from app.services.vulnerability import final_priority_score_for, hvi_score_for, readable_breakdown
from app.web import templates


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    disasters = list((await db.execute(
        select(Disaster).where(Disaster.status == "Active")
    )).scalars().all())
    priority_queue = await rerank_pending_requests(db)
    for emergency in priority_queue:
        emergency.hvi_factor_labels = readable_breakdown(emergency)
        emergency.display_hvi_score = hvi_score_for(emergency)
        emergency.display_final_priority_score = final_priority_score_for(emergency)
    await db.commit()

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
            "current_tab": "dashboard",
        },
    )
