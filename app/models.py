from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.database import Base

class Disaster(Base):
    __tablename__ = "disasters"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String, default="Medium")  # Critical, High, Medium, Low
    status = Column(String, default="Active")     # Active, Resolved
    affected_districts = Column(String, nullable=False)  # e.g., "Dhaka, Sylhet"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)  # e.g., "Flood Relief: Water Shortage"
    description = Column(Text, nullable=False)
    priority = Column(String, default="Medium")  # Critical, High, Medium, Low
    location = Column(String, nullable=False)    # e.g., "Dist. 4-A" or "Khulna"
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String, default="Pending")    # Pending, En Route, Completed, Canceled
    people_affected = Column(Integer, default=1)
    request_type = Column(String, default="Other")  # Medical Emergency, Flood Damage, Rescue, Food, Water, Other
    contact_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SupplyInventory(Base):
    __tablename__ = "supply_inventories"
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, unique=True, nullable=False)  # e.g., "MEDICAL KITS", "DRINKING WATER"
    quantity = Column(Integer, default=0)
    unit = Column(String, nullable=False)  # e.g., "units", "L"
    critical_threshold = Column(Integer, default=100)

class PersonnelStatus(Base):
    __tablename__ = "personnel_statuses"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, unique=True, nullable=False)  # e.g., "First Responders", "Medical Staff"
    active_count = Column(Integer, default=0)
    total_needed = Column(Integer, default=100)

class MissingPerson(Base):
    __tablename__ = "missing_persons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="Searching")  # Searching, In Hospital, Found & Safe
    age = Column(Integer, nullable=True)
    height = Column(String, nullable=True)        # e.g., "80cm" or "165cm"
    condition = Column(String, nullable=True)     # e.g., "Stable", "Critical: Diabetic"
    last_seen_location = Column(String, nullable=False)  # e.g., "Central Road, Cumilla"
    photo_url = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class FamilyUpdate(Base):
    __tablename__ = "family_updates"
    id = Column(Integer, primary_key=True, index=True)
    author = Column(String, nullable=False)  # e.g., "Ali Family", "Volunteer Team 4"
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DamageReport(Base):
    __tablename__ = "damage_reports"
    id = Column(Integer, primary_key=True, index=True)
    damage_type = Column(String, nullable=False)  # e.g., "Broken Road", "Flooding", "Fire Hazard", "Power Outage"
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="Reported")   # Reported, Verified, Resolved
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Donation(Base):
    __tablename__ = "donations"
    id = Column(Integer, primary_key=True, index=True)
    donor_name = Column(String, nullable=False)  # Name of the individual or NGO
    donor_contact = Column(String, nullable=True)  # Contact details
    item_name = Column(String, nullable=True)  # e.g., Food, Medicine, Clothes, Water, Blankets
    item_type = Column(String, nullable=True)  # e.g., Food, Medicine, Water
    quantity = Column(Integer, default=1)
    unit = Column(String, nullable=True)  # e.g., kg, units, liters
    location = Column(String, nullable=True)  # Where the donation is available
    status = Column(String, default="Available")  # Available, Allocated, Distributed
    created_at = Column(DateTime, default=datetime.utcnow)

class Shelter(Base):
    __tablename__ = "shelters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Name of the shelter
    location = Column(String, nullable=True)  # Address or general location
    capacity_total = Column(Integer, default=0)  # Total capacity
    capacity_available = Column(Integer, default=0)  # Currently available beds
    capacity_beds = Column(Integer, default=0)
    available_beds = Column(Integer, default=0)
    food_stock_days = Column(Integer, default=0)
    contact_details = Column(String, nullable=True)  # Phone, email, etc.
    contact_number = Column(String, nullable=True)
    facilities = Column(String, nullable=True)  # Comma-separated list of facilities
    food_stock = Column(String, nullable=True)  # Description of current food stock
    status = Column(String, default="Open")  # Open, Full, Closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class CommunityResource(Base):
    __tablename__ = "community_resources"
    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(String, nullable=False) # e.g. "Emergency Boat", "Power Generator", "Water Pump", "Solar Station"
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String, default="Available") # Available, Active, Maintenance

class Volunteer(Base):
    __tablename__ = "volunteers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    skills = Column(String, nullable=False) # e.g., "Medical", "Boat Operator", "Logistics", "Rescue"
    vehicle = Column(String, default="None") # Boat, Truck, Motorcycle, None
    distance_km = Column(Float, default=0.0)
    match_score = Column(Integer, default=80) # Matching score percentage
    status = Column(String, default="Available") # Available, Dispatched, Offline

class ReliefDistribution(Base):
    __tablename__ = "relief_distributions"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    organization = Column(String, nullable=False) # e.g. "Global Aid Network"
    district = Column(String, nullable=False) # e.g. "Cumilla"
    resource_type = Column(String, nullable=False) # e.g. "Food Kits", "Med-Packs"
    resource_quantity = Column(Integer, default=0)
    beneficiaries_count = Column(Integer, default=0)
    status = Column(String, default="Verified") # Verified, Duplicate Flag
