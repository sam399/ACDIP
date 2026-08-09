import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlalchemy import select
from app.database import SessionLocal
from app.models import EmergencyRequest
import io

@pytest.mark.asyncio
async def test_sos_page_renders():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/sos")
    assert response.status_code == 200
    assert "Submit Relief Request" in response.text
    assert "My Requests" in response.text
    assert "Emergency Request" in response.text

@pytest.mark.asyncio
async def test_sos_form_submission_no_photo():
    transport = ASGITransport(app=app)
    form_data = {
        "full_name": "Test Citizen",
        "phone_number": "+8801999888777",
        "location": "Dhaka Center",
        "people_affected": "3",
        "request_type": "Rescue Service",
        "description": "Trapped in flood waters near test sector.",
        "latitude": "23.8103",
        "longitude": "90.4125"
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/sos/submit", data=form_data)
        
    assert response.status_code == 303
    assert "my_requests" in response.cookies
    cookie_val = response.cookies["my_requests"]
    assert cookie_val.isdigit() or "," in cookie_val

    # Verify database record
    async with SessionLocal() as db:
        res = await db.execute(select(EmergencyRequest).where(EmergencyRequest.contact_name == "Test Citizen"))
        req = res.scalars().first()
        assert req is not None
        assert "Trapped in flood waters near test sector." in req.description
        assert req.people_affected == 3
        assert req.latitude == 23.8103

@pytest.mark.asyncio
async def test_sos_form_submission_with_photo():
    transport = ASGITransport(app=app)
    form_data = {
        "full_name": "Photo Test Citizen",
        "phone_number": "+8801777666555",
        "location": "Sylhet Sadar",
        "people_affected": "1",
        "request_type": "Food & Water",
        "description": "Need dry food packages."
    }
    
    # Mock file upload
    file_payload = {"photo": ("test_image.png", io.BytesIO(b"dummy image bytes"), "image/png")}
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/sos/submit", data=form_data, files=file_payload)
        
    assert response.status_code == 303
    assert "my_requests" in response.cookies
    
    # Verify in DB and file exists
    async with SessionLocal() as db:
        res = await db.execute(select(EmergencyRequest).where(EmergencyRequest.contact_name == "Photo Test Citizen"))
        req = res.scalars().first()
        assert req is not None
        assert req.photo_url is not None
        assert "/static/uploads/" in req.photo_url
