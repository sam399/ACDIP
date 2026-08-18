from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.common import utc_now


class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, default="Medium")
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String, default="Pending")
    people_affected = Column(Integer, default=1)

    # Household Vulnerability Index inputs and auditable outputs.
    elderly_members = Column(Integer, default=0)
    children = Column(Integer, default=0)
    pregnant_women = Column(Integer, default=0)
    members_with_disabilities = Column(Integer, default=0)
    members_with_chronic_illness = Column(Integer, default=0)
    hvi_raw_score = Column(Integer, default=0)
    hvi_score = Column(Integer, default=0)
    hvi_breakdown = Column(Text, nullable=True)

    # AI urgency, combined dispatch score, and current manual override.
    ai_priority = Column(String, default="Medium")
    ai_urgency_score = Column(Integer, default=50)
    final_priority_score = Column(Float, default=30.0)
    priority_rank = Column(Integer, nullable=True)
    priority_override = Column(String, nullable=True)
    override_justification = Column(Text, nullable=True)
    override_updated_at = Column(DateTime, nullable=True)
    trust_score = Column(Integer, default=100, nullable=False)
    trust_breakdown = Column(Text, nullable=True)

    request_type = Column(String, default="Other")
    contact_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    vulnerability_assessment = relationship(
        "HouseholdVulnerabilityAssessment",
        back_populates="request",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    override_history = relationship(
        "PriorityOverride",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="PriorityOverride.created_at",
        lazy="selectin",
    )
