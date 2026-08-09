import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
from app.database import Base
from app.models import Disaster, EmergencyRequest, SupplyInventory, PersonnelStatus, MissingPerson, FamilyUpdate

async def seed():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    # Drop and recreate tables to ensure fresh state
    async with engine.begin() as conn:
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
        
        # 5. Seed missing persons (Figma Design Matches)
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
        
        await session.commit()
    print("Database successfully seeded with Figma design mock data!")

if __name__ == "__main__":
    asyncio.run(seed())
