from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Shelter
from app.config import settings

# Attempt import of Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

async def get_chatbot_response(message: str, db: AsyncSession) -> str:
    message_lower = message.lower()
    
    # 1. Fallback heuristic keyword response builder
    # Query active shelters dynamically for the response
    shelter_query = await db.execute(select(Shelter))
    shelters = shelter_query.scalars().all()
    shelter_names = ", ".join(s.name for s in shelters) if shelters else "Tongi Shelter"
    
    contacts_info = "National Emergency: 999, Disaster Helpdesk: 333, Dhaka Center Command: +8801999888777"
    
    flood_tips = (
        "Flood Safety advice:\n"
        "1. Disconnect all electrical appliances if water levels rise.\n"
        "2. Do not swim, walk, or drive through flood waters.\n"
        "3. Boil all drinking water to prevent contamination.\n"
        "4. Move valuables to higher floors."
    )
    
    cyclone_tips = (
        "Cyclone Preparedness rules:\n"
        "1. Secure loose window shutters and outdoor items.\n"
        "2. Keep a survival kit ready (dry food, flashlight, power bank).\n"
        "3. Move to the nearest designated cyclone shelter immediately when warnings are issued."
    )
    
    distribution_info = "Food & water distributions are active at Dhaka Mirpur Shelter and Kurigram Camp B. Please check 'My Requests' to see if a dispatch is scheduled."

    # Pattern matches
    if "shelter" in message_lower or "accommodation" in message_lower:
        return f"The nearest active shelters are: {shelter_names}. You can view bed availabilities in the Shelters page."
    elif "contact" in message_lower or "phone" in message_lower or "number" in message_lower:
        return f"Emergency helpline contacts:\n{contacts_info}."
    elif "flood" in message_lower or "water" in message_lower:
        return flood_tips
    elif "cyclone" in message_lower or "storm" in message_lower:
        return cyclone_tips
    elif "food" in message_lower or "distribution" in message_lower or "relief" in message_lower:
        return distribution_info

    # 2. If Gemini is available and key is set, use AI
    if HAS_GEMINI and settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            system_context = (
                f"You are the RESPOND-ER AI Assistant. Answer citizen query concisely in the context of Bangladesh floods. "
                f"Nearest active shelters: {shelter_names}. "
                f"Contacts: {contacts_info}. "
                f"Distribution sites: {distribution_info}. "
                f"User Message: {message}"
            )
            response = model.generate_content(system_context)
            if response and response.text:
                return response.text.strip()
        except Exception:
            pass # Fallback to default message on failure
            
    return (
        "I am here to assist you with emergency questions. "
        "Try asking about: nearest shelters, safety instructions (flood/cyclone), emergency contacts, or relief distribution points."
    )
