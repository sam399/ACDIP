import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Volunteer

@pytest.mark.asyncio
async def test_resources_page():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/resources")
    assert response.status_code == 200
    assert "Community Resource Map" in response.text
    assert "NGO Inventory" in response.text
    assert "Surgical Masks" in response.text
    assert "Water Tabs" in response.text

@pytest.mark.asyncio
async def test_shelters_page():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/shelters")
    assert response.status_code == 200
    assert "Smart Volunteer Matching" in response.text
    assert "Dr. Zakir" in response.text
    assert "Mr Raju" in response.text
    assert "Chattogram Recreation Center" in response.text

@pytest.mark.asyncio
async def test_tracking_page():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/tracking")
    assert response.status_code == 200
    assert "Relief Fairness Dashboard" in response.text
    assert "Distribution Fairness Map" in response.text
    assert "Global Aid Network" in response.text
    assert "Duplicate Flag" in response.text

@pytest.mark.asyncio
async def test_resources_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/resources")
    assert response.status_code == 200
    data = response.json()
    assert "resources" in data
    assert len(data["resources"]) >= 6
    types = [r["type"] for r in data["resources"]]
    assert "Emergency Boat" in types
    assert "Power Generator" in types

@pytest.mark.asyncio
async def test_volunteer_dispatch_api():
    transport = ASGITransport(app=app)
    
    # Toggle volunteer 1 status to dispatched
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/volunteer/dispatch/1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["volunteer_status"] == "Dispatched"
    
    # Verify in database
    async with SessionLocal() as db:
        res = await db.execute(select(Volunteer).where(Volunteer.id == 1))
        vol = res.scalars().first()
        assert vol is not None
        assert vol.status == "Dispatched"
        
    # Toggle back to available
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_back = await ac.post("/api/volunteer/dispatch/1")
    assert response_back.status_code == 200
    data_back = response_back.json()
    assert data_back["volunteer_status"] == "Available"
