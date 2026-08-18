from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CommunityResource, Donation, ReliefDistribution, SupplyInventory, Volunteer
from app.models.common import utc_now
from app.web import templates


router = APIRouter()

INVENTORY_ITEMS = [
    {"item": "Surgical Masks", "location": "Central Warehouse", "stock": "12,400", "trend": "+ 12%"},
    {"item": "First Aid Kits", "location": "North Field Hub", "stock": "842", "trend": "- 5%"},
    {"item": "LED Torches", "location": "South Field Hub", "stock": "2,100", "trend": "--"},
    {"item": "Water Tabs", "location": "West Mobile Unit", "stock": "150,000", "trend": "+ 45%"},
]

INVENTORY_MAPPING = {
    "Medicine": ("Medical Kits", "kits"),
    "Water": ("Drinking Water", "L"),
    "Food": ("Emergency Meals", "meals"),
}


@router.get("/resources", response_class=HTMLResponse)
async def get_resources(request: Request, db: AsyncSession = Depends(get_db)):
    resources = list((await db.execute(select(CommunityResource))).scalars().all())
    counts = {
        "boats": sum(resource.resource_type == "Emergency Boat" for resource in resources),
        "generators": sum(resource.resource_type == "Power Generator" for resource in resources),
        "kitchens": sum(resource.resource_type == "Relief Kitchen" for resource in resources),
        "pumps": sum(resource.resource_type == "Water Pump" for resource in resources),
    }
    return templates.TemplateResponse(
        request=request,
        name="resources.html",
        context={
            "resources": resources,
            "counts": counts,
            "inventory_items": INVENTORY_ITEMS,
            "current_tab": "resources",
        },
    )


@router.post("/resources/donate", response_class=RedirectResponse)
async def submit_resource_donation(
    donor_name: str = Form(...),
    item_type: str = Form(...),
    quantity: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    db.add(Donation(
        donor_name=donor_name,
        item_name=item_type,
        item_type=item_type,
        quantity=quantity,
        status="Received",
        created_at=utc_now(),
    ))
    inventory_definition = INVENTORY_MAPPING.get(item_type)
    if inventory_definition:
        inventory_name, unit = inventory_definition
        inventory = await db.scalar(
            select(SupplyInventory).where(SupplyInventory.item_name == inventory_name)
        )
        if inventory:
            inventory.quantity += quantity
        else:
            db.add(SupplyInventory(
                item_name=inventory_name,
                quantity=quantity,
                unit=unit,
                critical_threshold=500,
            ))
    await db.commit()
    return RedirectResponse(url="/resources", status_code=303)


@router.get("/tracking", response_class=HTMLResponse)
async def get_tracking(request: Request, db: AsyncSession = Depends(get_db)):
    distributions = list((await db.execute(
        select(ReliefDistribution).order_by(ReliefDistribution.date.desc())
    )).scalars().all())
    flagged = [distribution for distribution in distributions if distribution.status == "Duplicate Flag"]
    return templates.TemplateResponse(
        request=request,
        name="tracking.html",
        context={
            "distributions": distributions,
            "total_flagged": len(flagged),
            "conflict_intercepts": sum(
                distribution.status == "Duplicate Flag" or distribution.resource_quantity >= 1000
                for distribution in distributions
            ),
            "estimated_savings": f"${sum(d.resource_quantity * 5 for d in flagged):,}" if flagged else "$0",
            "current_tab": "tracking",
        },
    )


@router.get("/api/resources")
async def get_resources_api(db: AsyncSession = Depends(get_db)):
    resources = (await db.execute(select(CommunityResource))).scalars().all()
    return {
        "resources": [
            {
                "id": resource.id,
                "type": resource.resource_type,
                "location": resource.location,
                "latitude": resource.latitude,
                "longitude": resource.longitude,
                "status": resource.status,
            }
            for resource in resources
        ]
    }


@router.post("/api/volunteer/dispatch/{volunteer_id}")
async def dispatch_volunteer(volunteer_id: int, db: AsyncSession = Depends(get_db)):
    volunteer = await db.get(Volunteer, volunteer_id)
    if not volunteer:
        return {"status": "error", "message": "Volunteer not found"}
    volunteer.status = "Dispatched" if volunteer.status == "Available" else "Available"
    await db.commit()
    return {"status": "success", "volunteer_status": volunteer.status, "id": volunteer.id}
