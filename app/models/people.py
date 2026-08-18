from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database import Base
from app.models.common import utc_now


class PersonnelStatus(Base):
    __tablename__ = "personnel_statuses"

    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, unique=True, nullable=False)
    active_count = Column(Integer, default=0)
    total_needed = Column(Integer, default=100)


class MissingPerson(Base):
    __tablename__ = "missing_persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="Searching")
    age = Column(Integer, nullable=True)
    height = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    last_seen_location = Column(String, nullable=False)
    photo_url = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class FamilyUpdate(Base):
    __tablename__ = "family_updates"

    id = Column(Integer, primary_key=True, index=True)
    author = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    skills = Column(String, nullable=False)
    vehicle = Column(String, default="None")
    distance_km = Column(Float, default=0.0)
    match_score = Column(Integer, default=80)
    status = Column(String, default="Available")
