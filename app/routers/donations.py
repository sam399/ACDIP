from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Donation, SupplyInventory
from app.models.common import utc_now
from app.presenters import render_donation_card
from app.web import templates


router = APIRouter()


@router.get("/donations", response_class=HTMLResponse)
async def get_donations(
    request: Request,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Donation)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            Donation.donor_name.ilike(pattern)
            | Donation.item_name.ilike(pattern)
            | Donation.location.ilike(pattern)
            | Donation.status.ilike(pattern)
        )
    donations = list((await db.execute(
        query.order_by(Donation.created_at.desc())
    )).scalars().all())
    return templates.TemplateResponse(
        request=request,
        name="donations.html",
        context={"donations": donations, "current_tab": "resources", "search": search or ""},
    )


@router.post("/donations/submit", response_class=HTMLResponse)
async def submit_donation(
    request: Request,
    donor_name: str = Form(...),
    donor_contact: str | None = Form(None),
    item_name: str = Form(...),
    quantity: int = Form(...),
    unit: str | None = Form(None),
    location: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    donation = Donation(
        donor_name=donor_name,
        donor_contact=donor_contact,
        item_name=item_name,
        quantity=quantity,
        unit=unit,
        location=location,
        status="Available",
        created_at=utc_now(),
    )
    db.add(donation)
    inventory = await db.scalar(
        select(SupplyInventory).where(SupplyInventory.item_name == item_name)
    )
    if inventory:
        inventory.quantity += quantity
    await db.commit()
    if request.headers.get("hx-request") == "true":
        return HTMLResponse(content=render_donation_card(donation))
    return RedirectResponse(url="/donations", status_code=303)
