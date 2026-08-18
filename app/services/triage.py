"""Emergency urgency analysis with an optional Gemini provider."""

import importlib.util
import json

from app.config import settings


PRIORITIES = ("Critical", "High", "Medium", "Low")
HAS_GEMINI = importlib.util.find_spec("google.generativeai") is not None


def fallback_rules_triage(description: str, people_affected: int, request_type: str) -> dict:
    """Classify urgency locally when the optional AI provider is unavailable."""
    description_lower = (description or "").lower()
    request_type_lower = (request_type or "").lower()
    is_medical = any(term in description_lower for term in (
        "bleed", "heart", "pain", "medical", "injured", "injury", "unconscious",
        "stroke", "diabetic", "doctor", "hospital", "oxygen",
    )) or "medical" in request_type_lower
    is_trapped = any(term in description_lower for term in (
        "trap", "drown", "flood", "roof", "water rising", "evacuate", "rescue", "sink", "boat",
    )) or "rescue" in request_type_lower
    is_fire = "fire" in description_lower or "burn" in description_lower or "fire" in request_type_lower
    is_vulnerable = any(term in description_lower for term in (
        "child", "baby", "infant", "pregnant", "elderly", "grandfather",
        "grandmother", "old man", "old woman", "disabled", "wheelchair",
    ))

    if (is_medical or is_trapped) and (people_affected >= 5 or is_vulnerable):
        return {
            "priority": "Critical",
            "reasoning": (
                "Urgent life-safety risk flagged: high medical/trapped indicators "
                f"with vulnerable individuals or {people_affected} people affected."
            ),
        }
    if is_medical or is_trapped or is_fire or people_affected >= 3:
        return {
            "priority": "High",
            "reasoning": (
                f"High priority: threat to safety or health detected ({request_type}) "
                f"affecting {people_affected} person(s)."
            ),
        }
    if is_vulnerable or "water" in description_lower or "food" in description_lower:
        return {
            "priority": "Medium",
            "reasoning": "Medium priority: resource shortage or vulnerability without an immediate life threat.",
        }
    return {
        "priority": "Low",
        "reasoning": "Low priority: standard administrative request or general inquiry.",
    }


async def analyze_emergency_priority(
    description: str,
    people_affected: int,
    request_type: str,
) -> dict:
    """Use Gemini when configured, otherwise use deterministic local rules."""
    if HAS_GEMINI and settings.GEMINI_API_KEY:
        try:
            # Lazy import avoids loading an optional, deprecated SDK when the
            # application is running in its normal offline configuration.
            import google.generativeai as genai

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            You are the emergency dispatcher triage engine for RESPOND-ER.
            Request type: {request_type}
            People affected: {people_affected}
            Description: {description}
            Return JSON with a priority of Critical, High, Medium, or Low and a
            concise reasoning string. Do not include any other fields.
            """
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"},
            )
            result = json.loads(response.text.strip())
            if result.get("priority") in PRIORITIES:
                return {
                    "priority": result["priority"],
                    "reasoning": result.get("reasoning", "AI classified priority level."),
                }
        except Exception as error:
            print(f"Gemini API error: {error}. Falling back to local triage rules.")
    return fallback_rules_triage(description, people_affected, request_type)
