from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.common import utc_now


class HouseholdVulnerabilityAssessment(Base):
    __tablename__ = "household_vulnerability_assessments"

    id = Column(Integer, primary_key=True)
    request_id = Column(
        Integer,
        ForeignKey("emergency_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    elderly_members = Column(Integer, nullable=False, default=0)
    children = Column(Integer, nullable=False, default=0)
    pregnant_women = Column(Integer, nullable=False, default=0)
    members_with_disabilities = Column(Integer, nullable=False, default=0)
    members_with_chronic_illness = Column(Integer, nullable=False, default=0)
    raw_score = Column(Integer, nullable=False, default=0)
    normalized_score = Column(Integer, nullable=False, default=0)
    breakdown = Column(Text, nullable=True)
    ai_priority = Column(String, nullable=False, default="Medium")
    ai_urgency_score = Column(Integer, nullable=False, default=50)
    final_priority_score = Column(Float, nullable=False, default=30.0)
    calculated_at = Column(DateTime, nullable=False, default=utc_now)

    request = relationship("EmergencyRequest", back_populates="vulnerability_assessment")


class PriorityOverride(Base):
    __tablename__ = "priority_overrides"

    id = Column(Integer, primary_key=True)
    request_id = Column(
        Integer,
        ForeignKey("emergency_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_priority = Column(String, nullable=True)
    new_priority = Column(String, nullable=False)
    justification = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    request = relationship("EmergencyRequest", back_populates="override_history")
