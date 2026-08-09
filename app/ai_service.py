import re
import json

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from app.config import settings

def fallback_rules_triage(description: str, people_affected: int, request_type: str) -> dict:
    """
    A local rule-based heuristic triage engine that acts as a developer fallback
    and offline backup when the Gemini API is unreachable or package isn't installed.
    """
    desc_lower = description.lower() if description else ""
    req_lower = request_type.lower() if request_type else ""
    
    # 1. Identify critical hazard patterns
    is_medical = any(x in desc_lower for x in ["bleed", "heart", "pain", "medical", "injured", "injury", "unconscious", "stroke", "diabetic", "doctor", "hospital", "oxygen"]) or "medical" in req_lower
    is_trapped = any(x in desc_lower for x in ["trap", "drown", "flood", "roof", "water rising", "evacuate", "rescue", "sink", "boat"]) or "rescue" in req_lower
    is_fire = "fire" in desc_lower or "burn" in desc_lower or "fire" in req_lower
    
    # 2. Identify vulnerable groups
    is_vulnerable = any(x in desc_lower for x in ["child", "baby", "infant", "pregnant", "elderly", "grandfather", "grandmother", "old man", "old woman", "disabled", "wheelchair"])

    # 3. Urgency rules
    if (is_medical or is_trapped) and (people_affected >= 5 or is_vulnerable):
        priority = "Critical"
        reasoning = f"Urgent life-safety risk flagged: high medical/trapped indicators with vulnerable individuals or {people_affected} people affected."
    elif is_medical or is_trapped or is_fire or people_affected >= 3:
        priority = "High"
        reasoning = f"High priority: threat to safety or health detected ({request_type}) affecting {people_affected} person(s)."
    elif is_vulnerable or "water" in desc_lower or "food" in desc_lower:
        priority = "Medium"
        reasoning = "Medium priority: request contains resource shortages or vulnerable indicators but no immediate life-threat."
    else:
        priority = "Low"
        reasoning = "Low priority: standard administrative request or general inquiry."

    return {
        "priority": priority,
        "reasoning": reasoning
    }

async def analyze_emergency_priority(description: str, people_affected: int, request_type: str) -> dict:
    """
    Analyzes citizen emergency reports using the Gemini API.
    Falls back to a keyword rules engine if API credentials or packages are missing.
    """
    if HAS_GEMINI and settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
            You are the AI emergency dispatcher triage engine for RESPOND-ER.
            Analyze the following emergency request from a citizen:
            - Request Type: {request_type}
            - Number of people affected: {people_affected}
            - Description: {description}
            
            Assign one of the following priority levels:
            - "Critical": Immediate threat to life, medical emergencies, trapped people, rising water with high vulnerability.
            - "High": Significant threat to health or safety, fire, large group affected, blocked key routes.
            - "Medium": Needs attention, food/water shortages, vulnerable individuals but no immediate life-safety threat.
            - "Low": General damage report, resource request with no urgency, standard status updates.
            
            Output your analysis strictly in valid JSON format:
            {{
              "priority": "Critical" | "High" | "Medium" | "Low",
              "reasoning": "A concise single-sentence summary of why this priority was assigned."
            }}
            """
            
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            result = json.loads(response.text.strip())
            if "priority" in result and result["priority"] in ["Critical", "High", "Medium", "Low"]:
                return {
                    "priority": result["priority"],
                    "reasoning": result.get("reasoning", "AI classified priority level.")
                }
        except Exception as e:
            print(f"Gemini API Error: {e}. Falling back to rules engine.")
            
    # Rules-engine fallback (for developer setup & offline reliability)
    return fallback_rules_triage(description, people_affected, request_type)
