import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_dashboard_route():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "RESPOND-ER" in response.text
    assert "Incident Control" in response.text
    # Verify that seeded database entities are rendered
    assert "Kurigram Inundation" in response.text
    assert "Flood Relief: Water Shortage" in response.text

@pytest.mark.asyncio
async def test_missing_persons_route():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/missing")
    assert response.status_code == 200
    assert "Missing" in response.text
    assert "Liza Akhter" in response.text
    assert "Sharmin Begum" in response.text
    assert "Ali Family" in response.text

@pytest.mark.asyncio
async def test_add_family_update():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/missing/update", data={
            "author": "Volunteer Unit 9",
            "message": "Automated testing verification check."
        })
    # Verification of redirect status code (303)
    assert response.status_code == 303
    
    # Follow redirect and verify update is listed
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_redirect = await ac.get("/missing")
    assert response_redirect.status_code == 200
    assert "Volunteer Unit 9" in response_redirect.text
    assert "Automated testing verification check." in response_redirect.text
