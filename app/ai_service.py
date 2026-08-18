"""Compatibility imports for the relocated triage service."""

from app.services.triage import HAS_GEMINI, analyze_emergency_priority, fallback_rules_triage

__all__ = ["HAS_GEMINI", "analyze_emergency_priority", "fallback_rules_triage"]
