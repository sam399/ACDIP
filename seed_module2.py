"""Safely add the Module 2 demo records without replacing existing data."""

import asyncio
from datetime import datetime

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import CommunityResource, ReliefDistribution, Volunteer


RESOURCES = [
    ("Emergency Boat", "Satkhira Dock A", 22.3500, 89.0800, "Available"),
    ("Emergency Boat", "Khulna River Terminal", 22.8456, 89.5403, "Active"),
    ("Power Generator", "Sylhet North Hospital", 24.8949, 91.8687, "Available"),
    ("Relief Kitchen", "Dhaka Mirpur Shelter", 23.8103, 90.4125, "Available"),
    ("Relief Kitchen", "Kurigram Camp B", 25.8054, 89.6300, "Available"),
    ("Water Pump", "Feni Sadar Station", 23.0159, 91.3976, "Available"),
]

VOLUNTEERS = [
    ("Dr. Zakir", "Medical", "None", 1.2, 98, "Available"),
    ("Mr Raju", "Boat Operator", "Boat", 3.5, 92, "Available"),
    ("Hridoy", "Logistics", "Motorcycle", 0.8, 89, "Available"),
]

DISTRIBUTIONS = [
    (datetime(2026, 7, 14), "Global Aid Network", "Cumilla", "Food Kits", 1200, 1150, "Verified"),
    (datetime(2026, 7, 7), "Red Cross Unit 4", "Chattogram", "Med-Packs", 450, 420, "Verified"),
    (datetime(2026, 7, 9), "Local Relief NGO", "Mymensingh", "Water Tabs", 2000, 800, "Duplicate Flag"),
    (datetime(2026, 7, 12), "ShelterNow Int.", "Rangpur", "Tents", 80, 320, "Verified"),
]


async def seed_module2(session) -> dict[str, int]:
    """Insert missing records using stable natural keys; never update or delete."""
    inserted = {"resources": 0, "volunteers": 0, "distributions": 0}

    for resource_type, location, latitude, longitude, status in RESOURCES:
        exists = await session.scalar(
            select(CommunityResource.id).where(
                CommunityResource.resource_type == resource_type,
                CommunityResource.location == location,
            )
        )
        if not exists:
            session.add(CommunityResource(
                resource_type=resource_type, location=location, latitude=latitude,
                longitude=longitude, status=status,
            ))
            inserted["resources"] += 1

    for name, skills, vehicle, distance_km, match_score, status in VOLUNTEERS:
        exists = await session.scalar(select(Volunteer.id).where(Volunteer.name == name))
        if not exists:
            session.add(Volunteer(
                name=name, skills=skills, vehicle=vehicle, distance_km=distance_km,
                match_score=match_score, status=status,
            ))
            inserted["volunteers"] += 1

    for date, organization, district, resource_type, quantity, beneficiaries, status in DISTRIBUTIONS:
        exists = await session.scalar(
            select(ReliefDistribution.id).where(
                ReliefDistribution.date == date,
                ReliefDistribution.organization == organization,
                ReliefDistribution.district == district,
                ReliefDistribution.resource_type == resource_type,
            )
        )
        if not exists:
            session.add(ReliefDistribution(
                date=date, organization=organization, district=district,
                resource_type=resource_type, resource_quantity=quantity,
                beneficiaries_count=beneficiaries, status=status,
            ))
            inserted["distributions"] += 1

    await session.flush()
    return inserted


async def main() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal.begin() as session:
        inserted = await seed_module2(session)
    print(
        "Module 2 seed complete: "
        f"{inserted['resources']} resources, "
        f"{inserted['volunteers']} volunteers, "
        f"{inserted['distributions']} distributions inserted."
    )


if __name__ == "__main__":
    asyncio.run(main())
