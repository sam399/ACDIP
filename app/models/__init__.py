"""Domain-grouped SQLAlchemy models.

Public re-exports keep existing imports stable while model definitions live in
focused modules.
"""

from app.models.disasters import DamageReport, Disaster, RecoveryBaseline, RecoveryMilestone
from app.models.emergencies import EmergencyRequest
from app.models.intelligence import HouseholdVulnerabilityAssessment, PriorityOverride
from app.models.people import FamilyUpdate, MissingPerson, PersonnelStatus, Volunteer
from app.models.resources import (
    CommunityResource,
    Donation,
    ReliefDistribution,
    Shelter,
    SupplyInventory,
)
from app.models.support import SupportTicket

__all__ = [
    "CommunityResource",
    "DamageReport",
    "Disaster",
    "Donation",
    "EmergencyRequest",
    "FamilyUpdate",
    "HouseholdVulnerabilityAssessment",
    "MissingPerson",
    "PersonnelStatus",
    "PriorityOverride",
    "RecoveryBaseline",
    "RecoveryMilestone",
    "ReliefDistribution",
    "Shelter",
    "SupplyInventory",
    "Volunteer",
    "SupportTicket",
]
