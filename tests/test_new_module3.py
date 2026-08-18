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


@pytest.mark.asyncio
async def test_language_switcher():
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/change-lang/bn", follow_redirects=False)
    assert response.status_code == 303
    assert "lang=bn" in response.headers.get("set-cookie", "")
    
    cookies = {"lang": "bn"}
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    # Checks for translated Bangla elements in navbar and metric boxes
    assert "ড্যাশবোর্ড" in response.text or "সক্রিয় ইভেন্ট" in response.text


@pytest.mark.asyncio
async def test_settings_and_support_endpoints():
    transport = ASGITransport(app=app)
    
    # 1. Verify Settings Page loads
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/settings")
    assert response.status_code == 200
    assert "Platform Settings" in response.text

    # 2. Verify Save Settings saves weights
    settings_data = {
        "ai_weight": "30",
        "hvi_weight": "70",
        "gemini_key": "test_key",
        "refresh_interval": "5",
        "dark_mode": "true"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/settings/save", data=settings_data, follow_redirects=False)
    assert response.status_code == 303
    cookies = response.headers.get("set-cookie", "")
    assert "ai_weight=30" in cookies
    assert "hvi_weight=70" in cookies
    assert "dark_mode=true" in cookies

    # 3. Verify Support Page loads
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/support")
    assert response.status_code == 200
    assert "Support Command Center" in response.text

    # 4. Verify support ticket submission
    ticket_data = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Drone Route Issue",
        "message": "Drone unable to find a clear path to sector 3."
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/support/submit", data=ticket_data, follow_redirects=False)
    assert response.status_code == 303

    # 5. Verify Audit Logs Page loads
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/audit-logs")
    assert response.status_code == 200
    assert "Audit Log Registry" in response.text



