import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlalchemy import select
from app.database import SessionLocal
from app.models import MissingPerson

@pytest.mark.asyncio
async def test_submit_missing_person_report():
    transport = ASGITransport(app=app)
    form_data = {
        "name": "Riya Sen",
        "status": "Searching",
        "age": "14",
        "height": "150cm",
        "condition": "Wearing a red jacket",
        "last_seen_location": "Sylhet Town",
        "contact_name": "Father",
        "contact_phone": "+8801888222333"
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/missing/report", data=form_data)
        
    assert response.status_code == 303
    
    # Verify database entry
    async with SessionLocal() as db:
        res = await db.execute(select(MissingPerson).where(MissingPerson.name == "Riya Sen"))
        person = res.scalars().first()
        assert person is not None
        assert person.age == 14
        assert person.status == "Searching"

@pytest.mark.asyncio
async def test_submit_found_person_report():
    transport = ASGITransport(app=app)
    form_data = {
        "name": "Unknown Boy",
        "status": "Found & Safe",
        "age": "8",
        "height": "110cm",
        "condition": "Discovered at relief camp",
        "last_seen_location": "Dhaka Central Shelter"
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/missing/report", data=form_data)
        
    assert response.status_code == 303
    
    # Verify database entry
    async with SessionLocal() as db:
        res = await db.execute(select(MissingPerson).where(MissingPerson.name == "Unknown Boy"))
        person = res.scalars().first()
        assert person is not None
        assert person.status == "Found & Safe"

@pytest.mark.asyncio
async def test_missing_page_search_filtering():
    transport = ASGITransport(app=app)
    
    # Test Name search
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/missing", params={"search": "Liza"})
    assert response.status_code == 200
    assert "Liza Akhter" in response.text
    assert "Sharmin Begum" not in response.text

    # Test Location search
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_loc = await ac.get("/missing", params={"search": "Wing"})
    assert response_loc.status_code == 200
    assert "Sharmin Begum" in response_loc.text
    assert "Liza Akhter" not in response_loc.text

@pytest.mark.asyncio
async def test_missing_page_status_filtering():
    transport = ASGITransport(app=app)
    
    # Test status checkbox filter (e.g. status is Searching)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/missing", params={"status": ["Searching"]})
    assert response.status_code == 200
    assert "Liza Akhter" in response.text
    assert "Sharmin Begum" not in response.text # since Sharmin is In Hospital
    assert "Leakot Haider" not in response.text # since Leakot is Found & Safe
