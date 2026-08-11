from fastapi import FastAPI, Depends, Request, Form, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import engine, Base, get_db, SessionLocal
from app.models import (
    Disaster, EmergencyRequest, SupplyInventory, PersonnelStatus, 
    MissingPerson, FamilyUpdate, DamageReport, Donation, Shelter, 
    CommunityResource, Volunteer, ReliefDistribution
)
from app.ai_service import analyze_emergency_priority
from datetime import datetime, UTC
import os
import shutil

app = FastAPI(title="RESPOND-ER Command Center")

# Ensure static directories exist
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/uploads", exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
async def startup():
    # Automatically create tables in local SQLite development
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- BACKGROUND AI TRIAGE TASK ---
async def run_ai_triage(request_id: int):
    async with SessionLocal() as db:
        req = await db.get(EmergencyRequest, request_id)
        if req:
            # Perform AI urgency and priority analysis
            triage = await analyze_emergency_priority(
                description=req.description,
                people_affected=req.people_affected,
                request_type=req.request_type
            )
            req.priority = triage["priority"]
            req.description = f"AI Dispatch: {triage['reasoning']}\n\n{req.description}"
            await db.commit()

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    # 1. Active Disasters
    disasters_query = await db.execute(select(Disaster).where(Disaster.status == "Active"))
    disasters = disasters_query.scalars().all()
    
    # 2. Emergency Requests for AI Priority Queue
    requests_query = await db.execute(
        select(EmergencyRequest)
        .where(EmergencyRequest.status != "Completed")
        .order_by(EmergencyRequest.priority == "Critical", EmergencyRequest.created_at.desc())
    )
    priority_queue = requests_query.scalars().all()
    
    # 3. Supply Inventory
    supplies_query = await db.execute(select(SupplyInventory))
    supplies = supplies_query.scalars().all()
    
    # 4. Personnel Status
    personnel_query = await db.execute(select(PersonnelStatus))
    personnel = personnel_query.scalars().all()
    
    # Calculate stats
    active_events_count = len(disasters)
    
    # Sum up affected districts (split by comma if stored as comma-separated)
    districts = set()
    for d in disasters:
        if d.affected_districts:
            for dist in d.affected_districts.split(","):
                districts.add(dist.strip())
    affected_districts_count = len(districts) if districts else 30 # fallback to 30 matching design
    
    total_requests_count = len(priority_queue)
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "disasters": disasters,
            "priority_queue": priority_queue,
            "supplies": supplies,
            "personnel": personnel,
            "active_events_count": active_events_count,
            "affected_districts_count": affected_districts_count,
            "total_requests_count": total_requests_count,
            "current_tab": "dashboard"
        }
    )

@app.get("/sos", response_class=HTMLResponse)
async def get_sos_page(request: Request, db: AsyncSession = Depends(get_db)):
    # Read client request IDs from cookies to populate "My Requests"
    my_requests_cookie = request.cookies.get("my_requests", "")
    my_requests = []
    
    if my_requests_cookie:
        try:
            ids = [int(x) for x in my_requests_cookie.split(",") if x.strip().isdigit()]
            if ids:
                query = await db.execute(
                    select(EmergencyRequest)
                    .where(EmergencyRequest.id.in_(ids))
                    .order_by(EmergencyRequest.created_at.desc())
                )
                my_requests = query.scalars().all()
        except Exception:
            pass # Ignore malformed cookies
            
    return templates.TemplateResponse(
        request=request,
        name="sos.html",
        context={
            "my_requests": my_requests,
            "current_tab": "sos"
        }
    )

@app.post("/sos/submit", response_class=RedirectResponse)
async def submit_sos_request(
    request: Request,
    background_tasks: BackgroundTasks,
    full_name: str = Form(...),
    phone_number: str = Form(...),
    location: str = Form(...),
    people_affected: int = Form(...),
    request_type: str = Form(...),
    description: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    photo: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    # Process optional photo upload
    photo_url = None
    if photo and photo.filename:
        filename = f"{int(datetime.now().timestamp())}_{photo.filename}"
        filepath = os.path.join("app/static/uploads", filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/static/uploads/{filename}"

    # Default description if not supplied
    if not description:
        description = f"Emergency request for {request_type.lower()} support."

    # Create new emergency request with a temporary "Pending Triage" state
    new_request = EmergencyRequest(
        title=f"{request_type}: {description[:30]}...",
        description=description,
        priority="Medium", # default initial priority before AI updates it
        location=location,
        latitude=latitude,
        longitude=longitude,
        status="Pending",
        people_affected=people_affected,
        request_type=request_type,
        contact_name=full_name,
        contact_phone=phone_number,
        photo_url=photo_url,
        created_at=datetime.now(UTC).replace(tzinfo=None)
    )
    
    db.add(new_request)
    await db.flush() # Populate new_request.id
    
    # Save request ID to cookies
    my_requests_cookie = request.cookies.get("my_requests", "")
    if my_requests_cookie:
        updated_cookie = f"{my_requests_cookie},{new_request.id}"
    else:
        updated_cookie = str(new_request.id)
        
    await db.commit()
    
    # Queue the AI triage background task
    background_tasks.add_task(run_ai_triage, new_request.id)
    
    response = RedirectResponse(url="/sos", status_code=303)
    response.set_cookie(key="my_requests", value=updated_cookie, max_age=3600*24*30) # 30 days
    return response

@app.post("/sos/damage", response_class=RedirectResponse)
async def submit_damage_report(
    damage_type: str = Form(...),
    location: str = Form(...),
    description: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    photo: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    # Process optional photo upload
    photo_url = None
    if photo and photo.filename:
        filename = f"{int(datetime.now().timestamp())}_dmg_{photo.filename}"
        filepath = os.path.join("app/static/uploads", filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/static/uploads/{filename}"

    # Default description
    if not description:
        description = f"Reported {damage_type.lower()} infrastructure damage."

    new_report = DamageReport(
        damage_type=damage_type,
        location=location,
        latitude=latitude,
        longitude=longitude,
        description=description,
        status="Reported",
        photo_url=photo_url,
        created_at=datetime.now(UTC).replace(tzinfo=None)
    )
    db.add(new_report)
    await db.commit()
    return RedirectResponse(url="/sos", status_code=303)

@app.get("/api/hazards")
async def get_hazards(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DamageReport).where(DamageReport.status != "Resolved"))
    reports = result.scalars().all()
    
    hazards = []
    for r in reports:
        if r.latitude and r.longitude:
            hazards.append({
                "id": r.id,
                "type": r.damage_type,
                "location": r.location,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "description": r.description,
                "status": r.status
            })
    return {"hazards": hazards}

@app.get("/missing", response_class=HTMLResponse)
async def get_missing_persons(
    request: Request, 
    search: str = None, 
    status: list[str] = Query(None), 
    db: AsyncSession = Depends(get_db)
):
    query = select(MissingPerson)
    
    # 1. Filter by status checkboxes
    if status and "All" not in status:
        query = query.where(MissingPerson.status.in_(status))
        
    # 2. Filter by search text (name or location)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (MissingPerson.name.like(search_pattern)) | 
            (MissingPerson.last_seen_location.like(search_pattern))
        )
        
    query = query.order_by(MissingPerson.created_at.desc())
    persons_result = await db.execute(query)
    missing_persons = persons_result.scalars().all()
    
    # Query family updates sidebar
    updates_result = await db.execute(select(FamilyUpdate).order_by(FamilyUpdate.created_at.desc()).limit(15))
    family_updates = updates_result.scalars().all()
    
    # Convert list of statuses to set for quick HTML check rendering
    selected_statuses = status or ["All"]
    
    return templates.TemplateResponse(
        request=request,
        name="missing_persons.html",
        context={
            "missing_persons": missing_persons,
            "family_updates": family_updates,
            "selected_statuses": selected_statuses,
            "search_query": search or "",
            "total_records": len(missing_persons),
            "current_tab": "missing_persons"
        }
    )

@app.post("/missing/report", response_class=RedirectResponse)
async def submit_missing_report(
    name: str = Form(...),
    status: str = Form(...), # Searching, In Hospital, Found & Safe
    age: int = Form(None),
    height: str = Form(None),
    condition: str = Form(None),
    last_seen_location: str = Form(...),
    photo: UploadFile = File(None),
    contact_name: str = Form(None),
    contact_phone: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    # Process optional photo upload
    photo_url = None
    if photo and photo.filename:
        filename = f"{int(datetime.now().timestamp())}_mp_{photo.filename}"
        filepath = os.path.join("app/static/uploads", filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/static/uploads/{filename}"

    new_person = MissingPerson(
        name=name,
        status=status,
        age=age,
        height=height,
        condition=condition,
        last_seen_location=last_seen_location,
        photo_url=photo_url,
        contact_name=contact_name,
        contact_phone=contact_phone,
        created_at=datetime.now(UTC).replace(tzinfo=None)
    )
    db.add(new_person)
    await db.commit()
    return RedirectResponse(url="/missing", status_code=303)

@app.post("/missing/update", response_class=RedirectResponse)
async def add_family_update(
    author: str = Form(...),
    message: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    new_update = FamilyUpdate(
        author=author,
        message=message,
        created_at=datetime.now(UTC).replace(tzinfo=None)
    )
    db.add(new_update)
    await db.commit()
    return RedirectResponse(url="/missing", status_code=303)

# --- MODULE 2 ROUTES ---

@app.get("/resources", response_class=HTMLResponse)
async def get_resources(request: Request, db: AsyncSession = Depends(get_db)):
    res_query = await db.execute(select(CommunityResource))
    resources = res_query.scalars().all()
    
    # Calculate aggregation counts for legend
    counts = {
        "boats": sum(1 for r in resources if r.resource_type == "Emergency Boat"),
        "generators": sum(1 for r in resources if r.resource_type == "Power Generator"),
        "kitchens": sum(1 for r in resources if r.resource_type == "Relief Kitchen"),
        "pumps": sum(1 for r in resources if r.resource_type == "Water Pump"),
    }
    
    # Query NGO inventories
    inventory_items = [
        {"item": "Surgical Masks", "location": "Central Warehouse", "stock": "12,400", "trend": "+ 12%"},
        {"item": "First Aid Kits", "location": "North Field Hub", "stock": "842", "trend": "- 5%"},
        {"item": "LED Torches", "location": "South Field Hub", "stock": "2,100", "trend": "--"},
        {"item": "Water Tabs", "location": "West Mobile Unit", "stock": "150,000", "trend": "+ 45%"}
    ]
    
    return templates.TemplateResponse(
        request=request,
        name="resources.html",
        context={
            "resources": resources,
            "counts": counts,
            "inventory_items": inventory_items,
            "current_tab": "resources"
        }
    )

@app.get("/shelters", response_class=HTMLResponse)
async def get_shelters(request: Request, db: AsyncSession = Depends(get_db)):
    vol_query = await db.execute(select(Volunteer).order_by(Volunteer.match_score.desc()))
    volunteers = vol_query.scalars().all()
    
    she_query = await db.execute(select(Shelter))
    shelters = she_query.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="shelters.html",
        context={
            "volunteers": volunteers,
            "shelters": shelters,
            "current_tab": "shelters"
        }
    )

@app.get("/tracking", response_class=HTMLResponse)
async def get_tracking(request: Request, db: AsyncSession = Depends(get_db)):
    dist_query = await db.execute(select(ReliefDistribution).order_by(ReliefDistribution.date.desc()))
    distributions = dist_query.scalars().all()
    
    # Statistics calculations
    total_flagged = sum(1 for d in distributions if d.status == "Duplicate Flag")
    conflict_intercepts = sum(1 for d in distributions if d.status == "Duplicate Flag" or d.resource_quantity >= 1000)
    estimated_savings = sum(d.resource_quantity * 5 for d in distributions if d.status == "Duplicate Flag") # mock math
    
    return templates.TemplateResponse(
        request=request,
        name="tracking.html",
        context={
            "distributions": distributions,
            "total_flagged": total_flagged,
            "conflict_intercepts": conflict_intercepts,
            "estimated_savings": f"${estimated_savings:,}" if estimated_savings else "$0",
            "current_tab": "tracking"
        }
    )

@app.get("/api/resources")
async def get_resources_api(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CommunityResource))
    resources = result.scalars().all()
    return {
        "resources": [
            {
                "id": r.id,
                "type": r.resource_type,
                "location": r.location,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "status": r.status
            } for r in resources
        ]
    }

@app.post("/api/volunteer/dispatch/{id}")
async def dispatch_volunteer(id: int, db: AsyncSession = Depends(get_db)):
    vol = await db.get(Volunteer, id)
    if not vol:
        return {"status": "error", "message": "Volunteer not found"}
    
    vol.status = "Dispatched" if vol.status == "Available" else "Available"
    await db.commit()
    return {"status": "success", "volunteer_status": vol.status, "id": vol.id}
