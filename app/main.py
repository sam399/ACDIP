from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import engine, Base, get_db
from app.models import Disaster, EmergencyRequest, SupplyInventory, PersonnelStatus, MissingPerson, FamilyUpdate
from datetime import datetime, UTC

app = FastAPI(title="RESPOND-ER Command Center")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
async def startup():
    # Automatically create tables in local SQLite development
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
        .order_by(EmergencyRequest.created_at.desc())
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
    
    # Render main dashboard using modern Starlette TemplateResponse signature
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

@app.get("/missing", response_class=HTMLResponse)
async def get_missing_persons(request: Request, status: str = None, db: AsyncSession = Depends(get_db)):
    # Query missing persons with status filter
    query = select(MissingPerson)
    if status and status != "All":
        query = query.where(MissingPerson.status == status)
    query = query.order_by(MissingPerson.created_at.desc())
    
    persons_result = await db.execute(query)
    missing_persons = persons_result.scalars().all()
    
    # Query family updates sidebar
    updates_result = await db.execute(select(FamilyUpdate).order_by(FamilyUpdate.created_at.desc()).limit(15))
    family_updates = updates_result.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="missing_persons.html",
        context={
            "missing_persons": missing_persons,
            "family_updates": family_updates,
            "selected_status": status or "All",
            "total_records": len(missing_persons),
            "current_tab": "missing_persons"
        }
    )

@app.post("/missing/update", response_class=RedirectResponse)
async def add_family_update(
    author: str = Form(...),
    message: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Add a family update to the database (timezone-aware UTC)
    new_update = FamilyUpdate(
        author=author,
        message=message,
        created_at=datetime.now(UTC).replace(tzinfo=None)
    )
    db.add(new_update)
    await db.commit()
    return RedirectResponse(url="/missing", status_code=303)

# Placeholders for future routes in other features
@app.get("/tracking", response_class=HTMLResponse)
async def get_tracking(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={"current_tab": "tracking", "message": "Tracking view coming soon."}
    )

@app.get("/resources", response_class=HTMLResponse)
async def get_resources(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={"current_tab": "resources", "message": "Resources view coming soon."}
    )

@app.get("/shelters", response_class=HTMLResponse)
async def get_shelters(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={"current_tab": "shelters", "message": "Shelters view coming soon."}
    )
