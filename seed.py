import asyncio
import argparse
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
from app.database import Base
from app.models import (
    Disaster, EmergencyRequest, SupplyInventory, PersonnelStatus, 
    MissingPerson, FamilyUpdate, DamageReport, Donation, Shelter, 
    CommunityResource, Volunteer, ReliefDistribution
)
from app.services.vulnerability import apply_vulnerability_scores
from datetime import datetime

async def seed(reset: bool = False):
    print(f"Connecting to database: {settings.URL if hasattr(settings, 'URL') else settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        existing_tables = set(await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names()))
        model_tables = {table.name for table in Base.metadata.sorted_tables}
        if existing_tables and not reset:
            missing_tables = model_tables - existing_tables
            if missing_tables:
                raise RuntimeError(
                    "Database schema is incomplete. Run `python -m alembic upgrade head` first."
                )
            populated_tables = await conn.run_sync(
                lambda sync_conn: [
                    table_name
                    for table_name in sorted(model_tables)
                    if sync_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one() > 0
                ]
            )
            if populated_tables:
                raise RuntimeError(
                    "Database already contains application data; refusing to overwrite it. "
                    "Use seed_module2.py for additive demo data or pass --reset explicitly."
                )
        if reset:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        # 1. Seed Active disasters
        disasters = [
            Disaster(title="Kurigram Inundation", severity="Critical", affected_districts="Kurigram", status="Active", latitude=25.8054, longitude=89.6300),
            Disaster(title="Sylhet Flash Flood", severity="High", affected_districts="Sylhet", status="Active", latitude=24.8949, longitude=91.8687),
            Disaster(title="Dhaka Chemical Store Fire", severity="High", affected_districts="Dhaka", status="Active", latitude=23.7115, longitude=90.4019),
            Disaster(title="Chittagong Port Fire", severity="Medium", affected_districts="Chittagong", status="Active", latitude=22.3569, longitude=91.7832),
            Disaster(title="Khulna Inundation", severity="Medium", affected_districts="Khulna", status="Active", latitude=22.8456, longitude=89.5403)
        ]
        session.add_all(disasters)
        
        # 2. Seed emergency requests (AI priority queue)
        requests = [
            EmergencyRequest(title="Flood Relief: Water Shortage", description="Shelter cluster in Satkhira reporting 4 hours of water supply remaining. 18 families affected.", priority="Critical", location="Dist. 4-A", status="Pending", people_affected=18, request_type="Water"),
            EmergencyRequest(title="Rescue: Rooftop Trapped", description="Family of 5 reported stranded on a rooftop in Khulna. Rising floodwaters at 1.5 ft/hr.", priority="High", location="Riverbend View", status="Pending", people_affected=5, request_type="Rescue")
        ]
        for emergency in requests:
            apply_vulnerability_scores(emergency, emergency.priority)
        session.add_all(requests)
        
        # 3. Seed personnel status
        personnel = [
            PersonnelStatus(role_name="First Responders", active_count=142, total_needed=150),
            PersonnelStatus(role_name="Medical Staff", active_count=68, total_needed=80),
            PersonnelStatus(role_name="Logistics Volunteers", active_count=210, total_needed=300)
        ]
        session.add_all(personnel)
        
        # 4. Seed supply inventory
        supplies = [
            SupplyInventory(item_name="Medical Kits", quantity=1240, unit="kits", critical_threshold=500),
            SupplyInventory(item_name="Drinking Water", quantity=420, unit="L", critical_threshold=1000),
            SupplyInventory(item_name="Emergency Meals", quantity=3100, unit="meals", critical_threshold=2000),
            SupplyInventory(item_name="Fuel Reserve", quantity=15200, unit="L", critical_threshold=5000)
        ]
        session.add_all(supplies)
        
        # 5. Seed missing persons
        missing = [
            MissingPerson(name="Liza Akhter", status="Searching", age=5, height="80cm", condition="Cumilla", last_seen_location="Central Road, Cumilla, 2 hours ago"),
            MissingPerson(name="Sharmin Begum", status="In Hospital", age=27, height="", condition="Condition: Stable", last_seen_location="DMC Medical Wing"),
            MissingPerson(name="Leakot Haider", status="Found & Safe", age=6, height="", condition="Case Closed", last_seen_location="Tongi"),
            MissingPerson(name="Munni Akhter", status="Searching", age=35, height="", condition="Critical: Diabetic", last_seen_location="Mymensingh Shelter, 4h ago")
        ]
        session.add_all(missing)
        
        # 6. Seed family updates
        updates = [
            FamilyUpdate(author="Ali Family", message="Riya was wearing a red jacket and carries her medication in a black bag. Please check near medical tents."),
            FamilyUpdate(author="Admin Responder", message="Zone B in Sylhet has been cleared. Moving search efforts to the Sirajgonj district."),
            FamilyUpdate(author="Haider Family", message="Thank you everyone! Leakot is safe and we are heading to the main shelter."),
            FamilyUpdate(author="Volunteer Team 4", message="Scanning CCTV footage from the North of Cumilla. Will update if Liza is spotted.")
        ]
        session.add_all(updates)

        # 7. Seed Damage Reports
        damages = [
            DamageReport(damage_type="Broken Road", location="Rajshahi Highway Bypass", latitude=24.3745, longitude=88.6042, description="Major road erosion blocking supply trucks.", status="Verified"),
            DamageReport(damage_type="Power Outage", location="Sylhet Sadar Substation", latitude=24.8949, longitude=91.8687, description="Power grid failure due to electrical lines submerged.", status="Reported"),
            DamageReport(damage_type="Flooding", location="Feni Town Center", latitude=23.0159, longitude=91.3976, description="Feni town completely waterlogged, levels rising.", status="Verified")
        ]
        session.add_all(damages)

        # 8. Seed Community Resources (Feature 7)
        resources = [
            CommunityResource(resource_type="Emergency Boat", location="Satkhira Dock A", latitude=22.3500, longitude=89.0800, status="Available"),
            CommunityResource(resource_type="Emergency Boat", location="Khulna River Terminal", latitude=22.8456, longitude=89.5403, status="Active"),
            CommunityResource(resource_type="Power Generator", location="Sylhet North Hospital", latitude=24.8949, longitude=91.8687, status="Available"),
            CommunityResource(resource_type="Relief Kitchen", location="Dhaka Mirpur Shelter", latitude=23.8103, longitude=90.4125, status="Available"),
            CommunityResource(resource_type="Relief Kitchen", location="Kurigram Camp B", latitude=25.8054, longitude=89.6300, status="Available"),
            CommunityResource(resource_type="Water Pump", location="Feni Sadar Station", latitude=23.0159, longitude=91.3976, status="Available")
        ]
        session.add_all(resources)

        # 9. Seed Volunteers (Feature 8)
        volunteers = [
            Volunteer(name="Dr. Zakir", skills="Medical", vehicle="None", distance_km=1.2, match_score=98, status="Available"),
            Volunteer(name="Mr Raju", skills="Boat Operator", vehicle="Boat", distance_km=3.5, match_score=92, status="Available"),
            Volunteer(name="Hridoy", skills="Logistics", vehicle="Motorcycle", distance_km=0.8, match_score=89, status="Available")
        ]
        session.add_all(volunteers)

        # 10. Seed Shelters (Feature 9 Placeholder)
        shelters = [
            Shelter(name="Chattogram Recreation Center", location="Chattogram", capacity_total=150, capacity_available=8, food_stock="2 days", contact_details="(555) 012-3456"),
            Shelter(name="TigerX Gym", location="Dhaka", capacity_total=200, capacity_available=140, food_stock="8 days", contact_details="(555) 987-6543"),
            Shelter(name="Paradise Community Hall", location="Khulna", capacity_total=100, capacity_available=25, food_stock="3 days", contact_details="(555) 234-5678")
        ]
        session.add_all(shelters)

        # 11. Seed Relief Distributions (Feature 10 & 11 logs)
        distributions = [
            ReliefDistribution(date=datetime(2026, 7, 14), organization="Global Aid Network", district="Cumilla", resource_type="Food Kits", resource_quantity=1200, beneficiaries_count=1150, status="Verified"),
            ReliefDistribution(date=datetime(2026, 7, 7), organization="Red Cross Unit 4", district="Chattogram", resource_type="Med-Packs", resource_quantity=450, beneficiaries_count=420, status="Verified"),
            ReliefDistribution(date=datetime(2026, 7, 9), organization="Local Relief NGO", district="Mymensingh", resource_type="Water Tabs", resource_quantity=2000, beneficiaries_count=800, status="Duplicate Flag"),
            ReliefDistribution(date=datetime(2026, 7, 12), organization="ShelterNow Int.", district="Rangpur", resource_type="Tents", resource_quantity=80, beneficiaries_count=320, status="Verified")
        ]
        session.add_all(distributions)
        
        await session.commit()
    await engine.dispose()
    print("Database successfully seeded with Figma design mock data!")


def stamp_database_head() -> None:
    """Mark a schema created from current metadata as the current baseline."""
    command.stamp(Config(str(settings.PROJECT_ROOT / "alembic.ini")), "head")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize RESPOND-ER demo data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Explicitly drop all existing tables before seeding (destructive).",
    )
    try:
        asyncio.run(seed(reset=parser.parse_args().reset))
        stamp_database_head()
    except RuntimeError as error:
        parser.exit(status=1, message=f"Seed aborted: {error}\n")
