import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from app.main import app
from app.database import SessionLocal
from app.models import EmergencyRequest, SupplyInventory

@pytest.mark.asyncio
async def test_chatbot_endpoints():
    transport = ASGITransport(app=app)
    
    # 1. Test Chatbot page loads
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/chatbot")
    assert response.status_code == 200
    assert "AI Disaster Assistant" in response.text

    # 2. Test chatbot response with shelter keyword
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/chatbot", data={"message": "Where is the nearest shelter?"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "shelter" in data["response"].lower()

    # 3. Test chatbot response with flood keyword
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/chatbot", data={"message": "Give me flood safety tips"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "safety" in data["response"].lower()

@pytest.mark.asyncio
async def test_emergency_trust_score_calculation():
    transport = ASGITransport(app=app)
    
    form_data = {
        "full_name": "Trust test reporter",
        "phone_number": "+8801912345678",
        "location": "Dhaka Sector 4",
        "people_affected": "3",
        "request_type": "Water",
        "description": "Very long description to satisfy the description details point count. Stranded, need clean drinking water.",
        "latitude": "23.8103",
        "longitude": "90.4125"
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/sos/submit", data=form_data)
    assert response.status_code == 303
    
    # Verify trust score was calculated and stored
    async with SessionLocal() as db:
        res = await db.execute(select(EmergencyRequest).where(EmergencyRequest.contact_name == "Trust test reporter"))
        req = res.scalars().first()
        assert req is not None
        # Should have base trust (20) + detailed description (20) = 40
        assert req.trust_score >= 40

@pytest.mark.asyncio
async def test_predictive_shortage_alerts():
    transport = ASGITransport(app=app)
    
    # Check dashboard loads with alerts enabled
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    # The template should render the predictive alerts panel if there are active demands
    assert "AI Predictive Resource Shortage" in response.text
