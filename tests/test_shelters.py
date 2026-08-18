import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from uuid import uuid4

from app.main import app
from app.database import SessionLocal
from app.models import Shelter


@pytest.mark.asyncio
async def test_shelters_page_renders():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/shelters")

    assert response.status_code == 200
    assert "Shelter Management" in response.text
    assert "Register New Shelter" in response.text
    assert "Current Shelters" in response.text


@pytest.mark.asyncio
async def test_shelters_search_filters_results():
    transport = ASGITransport(app=app)
    search_term = f"searchable-{uuid4().hex[:6]}"
    other_term = f"other-{uuid4().hex[:6]}"

    async with SessionLocal() as db:
        db.add(Shelter(
            name=search_term,
            location="Dhaka",
            capacity_total=50,
            capacity_available=25,
            contact_details="test@example.com",
            facilities="Kitchen",
            food_stock="Rice",
            status="Open"
        ))
        db.add(Shelter(
            name=other_term,
            location="Chittagong",
            capacity_total=40,
            capacity_available=10,
            contact_details="test@example.com",
            facilities="Medical Aid",
            food_stock="Water",
            status="Open"
        ))
        await db.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/shelters", params={"search": search_term})

    assert response.status_code == 200
    assert search_term in response.text
    assert other_term not in response.text


@pytest.mark.asyncio
async def test_shelter_form_submission_creates_record():
    transport = ASGITransport(app=app)
    unique_name = f"Test Shelter {uuid4().hex[:6]}"
    form_data = {
        "name": unique_name,
        "location": "Banani",
        "capacity_total": "80",
        "capacity_available": "40",
        "contact_details": "+8801888999000",
        "facilities": "Kitchen, Medical Aid",
        "food_stock": "Rice, Water",
        "status": "Open"
    }

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/shelters/submit", data=form_data)

    assert response.status_code == 200
    assert "Test Shelter" in response.text
    assert "Banani" in response.text

    async with SessionLocal() as db:
        result = await db.execute(select(Shelter).where(Shelter.name == unique_name).order_by(Shelter.id.desc()))
        shelter = result.scalars().first()

    assert shelter is not None
    assert shelter.location == "Banani"
    assert shelter.capacity_total == 80
    assert shelter.capacity_available == 40


@pytest.mark.asyncio
async def test_shelter_capacity_update_changes_value():
    transport = ASGITransport(app=app)

    async with SessionLocal() as db:
        shelter = Shelter(
            name="Capacity Test Shelter",
            location="Motijheel",
            capacity_total=50,
            capacity_available=20,
            contact_details="test@example.com",
            facilities="Restrooms",
            food_stock="Water",
            status="Open"
        )
        db.add(shelter)
        await db.commit()
        await db.refresh(shelter)
        shelter_id = shelter.id

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/shelters/update",
            data={"shelter_id": shelter_id, "capacity_available": "35"}
        )

    assert response.status_code == 200
    assert "35" in response.text

    async with SessionLocal() as db:
        updated_shelter = await db.get(Shelter, shelter_id)

    assert updated_shelter is not None
    assert updated_shelter.capacity_available == 35
