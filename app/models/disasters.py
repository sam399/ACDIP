from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.common import utc_now


class Disaster(Base):
    __tablename__ = "disasters"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String, default="Medium")
    status = Column(String, default="Active")
    affected_districts = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    recovery_baselines = relationship("RecoveryBaseline", back_populates="disaster")
    recovery_milestones = relationship("RecoveryMilestone", back_populates="disaster")


class DamageReport(Base):
    __tablename__ = "damage_reports"

    id = Column(Integer, primary_key=True, index=True)
    damage_type = Column(String, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="Reported")
    photo_url = Column(String, nullable=True)
    trust_score = Column(Integer, default=100, nullable=False)
    trust_breakdown = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class RecoveryBaseline(Base):
    __tablename__ = "recovery_baselines"
    __table_args__ = (
        UniqueConstraint("disaster_id", "district", "category"),
        CheckConstraint("estimated_total > 0", name="positive_estimated_total"),
    )

    id = Column(Integer, primary_key=True, index=True)
    disaster_id = Column(Integer, ForeignKey("disasters.id", ondelete="CASCADE"), nullable=False)
    district = Column(String, nullable=False)
    category = Column(String, nullable=False)
    estimated_total = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    disaster = relationship("Disaster", back_populates="recovery_baselines")


class RecoveryMilestone(Base):
    __tablename__ = "recovery_milestones"
    __table_args__ = (
        CheckConstraint("completed_count > 0", name="positive_completed_count"),
    )

    id = Column(Integer, primary_key=True, index=True)
    disaster_id = Column(Integer, ForeignKey("disasters.id", ondelete="CASCADE"), nullable=False)
    district = Column(String, nullable=False)
    category = Column(String, nullable=False)
    completed_count = Column(Integer, nullable=False)
    milestone_date = Column(Date, nullable=False)
    affected_area = Column(String, nullable=False)
    verification_notes = Column(Text, nullable=True)
    evidence_photo_url = Column(String, nullable=True)
    is_verified = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    disaster = relationship("Disaster", back_populates="recovery_milestones")
