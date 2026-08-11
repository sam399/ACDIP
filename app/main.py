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


def render_shelter_card(shelter: Shelter) -> str:
    badge_class = "bg-success" if shelter.status == "Open" else "bg-danger" if shelter.status == "Full" else "bg-secondary"
    return f"""
    <div class=\"card mb-2\">
        <div class=\"card-body\">
            <div class=\"d-flex justify-content-between align-items-start\">
                <div>
                    <h5 class=\"card-title mb-1\">{shelter.name}</h5>
                    <p class=\"card-text text-muted mb-1\">Location: {shelter.location}</p>
                    <p class=\"card-text mb-1\">Capacity: <strong>{shelter.capacity_available}</strong> / {shelter.capacity_total} beds available</p>
                    <p class=\"card-text mb-1\">Facilities: {shelter.facilities or 'N/A'}</p>
                    <p class=\"card-text mb-0\">Food Stock: {shelter.food_stock or 'N/A'}</p>
                    <small class=\"text-muted\">Contact: {shelter.contact_details or 'N/A'}</small>
                </div>
                <div class=\"text-end\">
                    <span class=\"badge {badge_class}\">{shelter.status}</span>
                </div>
            </div>
            <form hx-post=\"/shelters/update\" hx-target=\"closest .card\" hx-swap=\"outerHTML\" class=\"mt-2\">
                <input type=\"hidden\" name=\"shelter_id\" value=\"{shelter.id}\">
                <div class=\"input-group input-group-sm\">
                    <span class=\"input-group-text\">Beds</span>
                    <input type=\"number\" class=\"form-control\" name=\"capacity_available\" value=\"{shelter.capacity_available}\" min=\"0\" max=\"{shelter.capacity_total}\">
                    <button class=\"btn btn-outline-primary\" type=\"submit\">Update</button>
                </div>
            </form>
        </div>
    </div>
    """


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

@app.get("/donations", response_class=HTMLResponse)
async def get_donations(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Donation))
    donations = result.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="donations.html",
        context={
            "donations": donations,
            "current_tab": "resources"
        }
    )

@app.post("/donations/submit", response_class=RedirectResponse)
async def submit_donation(
    donor_name: str = Form(...),
    donor_contact: str = Form(None),
    item_name: str = Form(...),
    quantity: int = Form(...),
    unit: str = Form(None),
    location: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    new_donation = Donation(
        donor_name=donor_name,
        donor_contact=donor_contact,
        item_name=item_name,
        quantity=quantity,
        unit=unit,
        location=location,
        status="Available",
        created_at=datetime.now(UTC).replace(tzinfo=None)
    )
    db.add(new_donation)
    await db.commit()

    # Optionally, update SupplyInventory if item matches existing inventory
    try:
        inventory_result = await db.execute(select(SupplyInventory).where(SupplyInventory.item_name == item_name))
        existing_inventory_item = inventory_result.scalar_one_or_none()
        if existing_inventory_item:
            existing_inventory_item.quantity += quantity
            await db.commit()
    except Exception:
        # If item doesn't exist in inventory, ignore or log
        pass

    return RedirectResponse(url="/donations", status_code=303)

@app.get("/shelters", response_class=HTMLResponse)
async def get_shelters(request: Request, db: AsyncSession = Depends(get_db), search: str | None = None):
    query = select(Shelter)
    if search:
        search_term = f"%{search.strip()}%"
        query = query.where(
            (Shelter.name.ilike(search_term)) |
            (Shelter.location.ilike(search_term)) |
            (Shelter.facilities.ilike(search_term)) |
            (Shelter.food_stock.ilike(search_term)) |
            (Shelter.contact_details.ilike(search_term))
        )

    result = await db.execute(query.order_by(Shelter.name.asc()))
    shelters = result.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="shelters.html",
        context={
            "shelters": shelters,
            "current_tab": "shelters",
            "search": search or ""
        }
    )

@app.post("/shelters/submit", response_class=HTMLResponse)
async def submit_shelter(
    request: Request,
    name: str = Form(...),
    location: str = Form(...),
    capacity_total: int = Form(...),
    capacity_available: int = Form(...),
    contact_details: str = Form(None),
    facilities: str = Form(None),
    food_stock: str = Form(None),
    status: str = Form("Open"),
    db: AsyncSession = Depends(get_db)
):
    new_shelter = Shelter(
        name=name,
        location=location,
        capacity_total=capacity_total,
        capacity_available=capacity_available,
        contact_details=contact_details,
        facilities=facilities,
        food_stock=food_stock,
        status=status,
        created_at=datetime.now(UTC).replace(tzinfo=None),
        updated_at=datetime.now(UTC).replace(tzinfo=None)
    )
    db.add(new_shelter)
    await db.commit()

    return HTMLResponse(content=render_shelter_card(new_shelter))

@app.post("/shelters/update", response_class=HTMLResponse)
async def update_shelter_capacity(
    shelter_id: int = Form(...),
    capacity_available: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    shelter = await db.get(Shelter, shelter_id)
    if shelter:
        shelter.capacity_available = capacity_available
        shelter.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await db.commit()

    if shelter:
        return HTMLResponse(content=render_shelter_card(shelter))

    return HTMLResponse(content="")

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

@app.post("/resources/donate", response_class=RedirectResponse)
async def submit_donation(
    donor_name: str = Form(...),
    item_type: str = Form(...), # Food, Medicine, Clothes, Water, Blankets
    quantity: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # 1. Save Donation Record
    new_donation = Donation(
        donor_name=donor_name,
        item_type=item_type,
        quantity=quantity,
        status="Received",
        created_at=datetime.utcnow()
    )
    db.add(new_donation)
    
    # 2. Dynamically update SupplyInventory counters
    inventory_mapping = {
        "Medicine": "Medical Kits",
        "Water": "Drinking Water",
        "Food": "Emergency Meals"
    }
    
    if item_type in inventory_mapping:
        inv_name = inventory_mapping[item_type]
        result = await db.execute(select(SupplyInventory).where(SupplyInventory.item_name == inv_name))
        inv = result.scalars().first()
        if inv:
            inv.quantity += quantity
        else:
            # Fallback insertion
            new_inv = SupplyInventory(
                item_name=inv_name,
                quantity=quantity,
                unit="L" if item_type == "Water" else "kits" if item_type == "Medicine" else "meals",
                critical_threshold=500
            )
            db.add(new_inv)
            
    await db.commit()
    return RedirectResponse(url="/resources", status_code=303)

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
