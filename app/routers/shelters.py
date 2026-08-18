from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Shelter
from app.models.common import utc_now
from app.presenters import render_shelter_card
from app.web import templates


router = APIRouter()


@router.get("/shelters", response_class=HTMLResponse)
async def get_shelters(
    request: Request,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Shelter)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            Shelter.name.ilike(pattern)
            | Shelter.location.ilike(pattern)
            | Shelter.facilities.ilike(pattern)
            | Shelter.food_stock.ilike(pattern)
            | Shelter.contact_details.ilike(pattern)
        )
    shelters = list((await db.execute(
        query.order_by(Shelter.name.asc())
    )).scalars().all())
    return templates.TemplateResponse(
        request=request,
        name="shelters.html",
        context={"shelters": shelters, "current_tab": "shelters", "search": search or ""},
    )


@router.post("/shelters/submit", response_class=HTMLResponse)
async def submit_shelter(
    request: Request,
    name: str = Form(...),
    location: str = Form(...),
    capacity_total: int = Form(...),
    capacity_available: int = Form(...),
    contact_details: str | None = Form(None),
    facilities: str | None = Form(None),
    food_stock: str | None = Form(None),
    status: str = Form("Open"),
    db: AsyncSession = Depends(get_db),
):
    shelter = Shelter(
        name=name,
        location=location,
        capacity_total=capacity_total,
        capacity_available=capacity_available,
        contact_details=contact_details,
        facilities=facilities,
        food_stock=food_stock,
        status=status,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(shelter)
    await db.commit()
    return HTMLResponse(content=render_shelter_card(shelter))


@router.post("/shelters/update", response_class=HTMLResponse)
async def update_shelter_capacity(
    shelter_id: int = Form(...),
    capacity_available: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    shelter = await db.get(Shelter, shelter_id)
    if not shelter:
        return HTMLResponse(content="", status_code=404)
    shelter.capacity_available = capacity_available
    shelter.updated_at = utc_now()
    await db.commit()
    return HTMLResponse(content=render_shelter_card(shelter))
