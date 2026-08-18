import json
import math
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import EmergencyRequest, DamageReport

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float | None:
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    # Haversine formula
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def evaluate_trust_score(report, db: AsyncSession, is_emergency: bool = True) -> dict:
    factors = {
        "base_trust": 20,
        "photo_evidence": 0,
        "description_detail": 0,
        "nearby_corroboration": 0,
    }
    
    # 1. Photo Evidence (+30%)
    if report.photo_url:
        factors["photo_evidence"] = 30
        
    # 2. Detailed Description (+20%)
    desc = report.description or ""
    if len(desc.strip()) > 50:
        factors["description_detail"] = 20
    elif len(desc.strip()) > 20:
        factors["description_detail"] = 10
        
    # 3. Nearby Corroboration (+30%)
    nearby_matches = 0
    if report.latitude and report.longitude:
        if is_emergency:
            query = select(EmergencyRequest).where(EmergencyRequest.id != report.id)
        else:
            query = select(DamageReport).where(DamageReport.id != report.id)
            
        results = await db.execute(query)
        other_reports = results.scalars().all()
        
        for other in other_reports:
            if other.latitude and other.longitude:
                dist = calculate_distance(report.latitude, report.longitude, other.latitude, other.longitude)
                if dist is not None and dist <= 5.0:
                    nearby_matches += 1
                    
    if nearby_matches >= 3:
        factors["nearby_corroboration"] = 30
    elif nearby_matches >= 1:
        factors["nearby_corroboration"] = 15
        
    raw_total = sum(factors.values())
    trust_score = min(max(raw_total, 0), 100)
    
    return {
        "score": trust_score,
        "breakdown": factors
    }
