from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models import Disaster, RecoveryBaseline, RecoveryMilestone


@pytest.mark.asyncio
async def test_recovery_baseline_milestone_and_dashboard():
    async with SessionLocal() as db:
        disaster = (await db.execute(select(Disaster).order_by(Disaster.id))).scalars().first()
        disaster_id = disaster.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        baseline_response = await client.post("/admin/recovery/baselines", data={
            "disaster_id": disaster_id, "district": "Kurigram",
            "category": "schools_reopened", "estimated_total": 60,
        })
        assert baseline_response.status_code == 303

        milestone_response = await client.post("/admin/recovery/milestones", data={
            "disaster_id": disaster_id, "district": "Kurigram",
            "category": "schools_reopened", "completed_count": 42,
            "milestone_date": date.today().isoformat(), "affected_area": "Kurigram Sadar",
            "verification_notes": "Verified by district education office.",
        })
        assert milestone_response.status_code == 303

        dashboard = await client.get("/recovery", params={
            "disaster_id": disaster_id, "district": "Kurigram",
            "category": "schools_reopened",
        })
        assert dashboard.status_code == 200
        assert "42 / 60" in dashboard.text
        assert "70.0%" in dashboard.text
        assert "Kurigram Sadar" in dashboard.text

    async with SessionLocal() as db:
        assert (await db.execute(select(RecoveryBaseline))).scalars().first() is not None
        assert (await db.execute(select(RecoveryMilestone))).scalars().first().is_verified is True


@pytest.mark.asyncio
async def test_recovery_milestone_requires_matching_baseline():
    async with SessionLocal() as db:
        disaster = (await db.execute(select(Disaster).order_by(Disaster.id))).scalars().first()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/recovery/milestones", data={
            "disaster_id": disaster.id, "district": "Noakhali",
            "category": "roads_repaired", "completed_count": 1,
            "milestone_date": date.today().isoformat(), "affected_area": "Ward 2",
        })
    assert response.status_code == 422
    assert "baseline" in response.text.lower()


@pytest.mark.asyncio
async def test_recovery_allows_district_filter_with_empty_disaster():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/recovery", params={
            "disaster_id": "",
            "district": "Kurigram",
            "category": "",
        })

    assert response.status_code == 200
    assert "Recovery Progress Dashboard" in response.text
