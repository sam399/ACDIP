import pytest
from app.ai_service import fallback_rules_triage, analyze_emergency_priority
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlalchemy import select
from app.database import SessionLocal
from app.models import EmergencyRequest
import asyncio

def test_fallback_rules_triage_critical():
    # Test high medical priority with children/vulnerability
    result = fallback_rules_triage(
        description="A young child is bleeding heavily from an injury, need a doctor immediately.",
        people_affected=1,
        request_type="Medical Emergency"
    )
    assert result["priority"] == "Critical"
    assert "Urgent" in result["reasoning"]

    # Test trapped in flood
    result = fallback_rules_triage(
        description="Family trapped on the roof, water rising fast.",
        people_affected=5,
        request_type="Rescue Service"
    )
    assert result["priority"] == "Critical"

def test_fallback_rules_triage_high():
    # Test standard medical without vulnerability
    result = fallback_rules_triage(
        description="Adult has a sprained ankle, is stable but needs checkup.",
        people_affected=1,
        request_type="Medical Emergency"
    )
    assert result["priority"] == "High"

    # Test fire event
    result = fallback_rules_triage(
        description="Electrical fire in the neighborhood.",
        people_affected=1,
        request_type="Fire Hazard"
    )
    assert result["priority"] == "High"

def test_fallback_rules_triage_medium_and_low():
    # Test supply requests
    result = fallback_rules_triage(
        description="Shelter needs additional blankets and water bottles.",
        people_affected=2,
        request_type="Food & Water"
    )
    assert result["priority"] == "Medium"

    # Test general inquiry
    result = fallback_rules_triage(
        description="Asking about status of relief camps.",
        people_affected=1,
        request_type="Other"
    )
    assert result["priority"] == "Low"

@pytest.mark.asyncio
async def test_endpoint_async_ai_triage():
    transport = ASGITransport(app=app)
    form_data = {
        "full_name": "Triage Tester",
        "phone_number": "+8801555444333",
        "location": "Dhaka Center",
        "people_affected": "6",
        "request_type": "Rescue Service",
        "description": "Six people are drowning and trapped under the bridge."
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/sos/submit", data=form_data)
        
    assert response.status_code == 303
    
    # Wait briefly for the background task to execute
    await asyncio.sleep(1.0)
    
    # Verify the database entry has updated to "Critical" priority and description is modified
    async with SessionLocal() as db:
        res = await db.execute(select(EmergencyRequest).where(EmergencyRequest.contact_name == "Triage Tester"))
        req = res.scalars().first()
        assert req is not None
        assert req.priority == "Critical"
        assert "AI Dispatch" in req.description
