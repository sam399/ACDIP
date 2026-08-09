import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlalchemy import select
from app.database import SessionLocal
from app.models import DamageReport

@pytest.mark.asyncio
async def test_submit_damage_report():
    transport = ASGITransport(app=app)
    form_data = {
        "damage_type": "Bridge Collapse",
        "location": "Mymensingh Local Bridge",
        "description": "Bridge washed away by high currents.",
        "latitude": "24.7471",
        "longitude": "90.4203"
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/sos/damage", data=form_data)
        
    assert response.status_code == 303
    
    # Verify database entry
    async with SessionLocal() as db:
        res = await db.execute(select(DamageReport).where(DamageReport.damage_type == "Bridge Collapse"))
        rep = res.scalars().first()
        assert rep is not None
        assert rep.location == "Mymensingh Local Bridge"
        assert rep.latitude == 24.7471

@pytest.mark.asyncio
async def test_get_hazards_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/hazards")
        
    assert response.status_code == 200
    data = response.json()
    assert "hazards" in data
    assert len(data["hazards"]) >= 3
    # Check seeded values
    types = [h["type"] for h in data["hazards"]]
    assert "Broken Road" in types
    assert "Power Outage" in types
