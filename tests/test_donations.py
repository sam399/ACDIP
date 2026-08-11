import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models import Donation


@pytest.mark.asyncio
async def test_donations_page_renders():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/donations")

    assert response.status_code == 200
    assert "Donation Management" in response.text
    assert "Submit New Donation" in response.text


@pytest.mark.asyncio
async def test_donation_form_submission_creates_record():
    transport = ASGITransport(app=app)
    form_data = {
        "donor_name": "Test Donor",
        "donor_contact": "+8801711223344",
        "item_name": "Food",
        "quantity": "20",
        "unit": "boxes",
        "location": "Uttara"
    }

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/donations/submit", data=form_data)

    assert response.status_code == 303

    async with SessionLocal() as db:
        result = await db.execute(select(Donation).where(Donation.donor_name == "Test Donor"))
        donation = result.scalars().first()

    assert donation is not None
    assert donation.item_name == "Food"
    assert donation.quantity == 20
    assert donation.location == "Uttara"
