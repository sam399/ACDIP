from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import SupplyInventory, EmergencyRequest, Shelter

async def calculate_predictive_shortages(db: AsyncSession) -> list[dict]:
    alerts = []
    
    # 1. Fetch active emergency requests
    req_query = await db.execute(select(EmergencyRequest).where(EmergencyRequest.status != "Completed"))
    active_requests = req_query.scalars().all()
    
    people_needing_water = sum(r.people_affected for r in active_requests if "water" in r.request_type.lower())
    people_needing_food = sum(r.people_affected for r in active_requests if "food" in r.request_type.lower() or "meal" in r.request_type.lower())
    people_needing_medical = sum(r.people_affected for r in active_requests if "medical" in r.request_type.lower())
    
    # 2. Fetch inventories
    inv_query = await db.execute(select(SupplyInventory))
    inventories = {i.item_name.lower(): i for i in inv_query.scalars().all()}
    
    # A. Water Shortage Calculation (3 liters per person per day)
    water_inv = inventories.get("drinking water")
    if water_inv and people_needing_water > 0:
        daily_consumption = people_needing_water * 3.0
        remaining_hours = (water_inv.quantity / daily_consumption) * 24.0
        if remaining_hours < 72.0:
            alerts.append({
                "type": "Water",
                "severity": "Critical" if remaining_hours < 24.0 else "Warning",
                "message": f"Drinking Water is predicted to deplete in {remaining_hours:.1f} hours based on current SOS demand ({people_needing_water} people affected)."
            })
            
    # B. Food Shortage Calculation (3 meals per person per day)
    food_inv = inventories.get("emergency meals")
    if food_inv and people_needing_food > 0:
        daily_consumption = people_needing_food * 3.0
        remaining_hours = (food_inv.quantity / daily_consumption) * 24.0
        if remaining_hours < 72.0:
            alerts.append({
                "type": "Food",
                "severity": "Critical" if remaining_hours < 24.0 else "Warning",
                "message": f"Emergency Meals are predicted to deplete in {remaining_hours:.1f} hours based on current SOS demand ({people_needing_food} people affected)."
            })
            
    # C. Medical Kits Shortage Calculation (0.1 kits per person per day)
    med_inv = inventories.get("medical kits")
    if med_inv and people_needing_medical > 0:
        daily_consumption = people_needing_medical * 0.1
        remaining_hours = (med_inv.quantity / daily_consumption) * 24.0
        if remaining_hours < 72.0:
            alerts.append({
                "type": "Medicine",
                "severity": "Critical" if remaining_hours < 24.0 else "Warning",
                "message": f"Medical Kits are predicted to deplete in {remaining_hours:.1f} hours based on current SOS demand ({people_needing_medical} people affected)."
            })
            
    # 3. Shelter Overcrowding Calculation
    shelter_query = await db.execute(select(Shelter))
    shelters = shelter_query.scalars().all()
    for s in shelters:
        occupancy = s.capacity_total - s.capacity_available
        occupancy_rate = (occupancy / s.capacity_total) * 100 if s.capacity_total > 0 else 0
        if occupancy_rate >= 85.0:
            alerts.append({
                "type": "Shelter",
                "severity": "Critical" if occupancy_rate >= 95.0 else "Warning",
                "message": f"Shelter '{s.name}' is experiencing high alert overcrowding (Occupancy: {occupancy_rate:.1f}%)."
            })
            
    return alerts
