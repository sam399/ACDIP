from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database import Base
from app.models.common import utc_now


class SupplyInventory(Base):
    __tablename__ = "supply_inventories"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, unique=True, nullable=False)
    quantity = Column(Integer, default=0)
    unit = Column(String, nullable=False)
    critical_threshold = Column(Integer, default=100)


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    donor_name = Column(String, nullable=False)
    donor_contact = Column(String, nullable=True)
    item_name = Column(String, nullable=True)
    item_type = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    unit = Column(String, nullable=True)
    location = Column(String, nullable=True)
    status = Column(String, default="Available")
    created_at = Column(DateTime, default=utc_now)


class Shelter(Base):
    __tablename__ = "shelters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)

    capacity_total = Column(Integer, default=0)
    capacity_available = Column(Integer, default=0)
    contact_details = Column(String, nullable=True)
    facilities = Column(String, nullable=True)
    food_stock = Column(String, nullable=True)
    status = Column(String, default="Open")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class CommunityResource(Base):
    __tablename__ = "community_resources"

    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(String, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String, default="Available")


class ReliefDistribution(Base):
    __tablename__ = "relief_distributions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=utc_now)
    organization = Column(String, nullable=False)
    district = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_quantity = Column(Integer, default=0)
    beneficiaries_count = Column(Integer, default=0)
    status = Column(String, default="Verified")
