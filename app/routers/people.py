from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import FamilyUpdate, MissingPerson
from app.models.common import utc_now
from app.web import save_upload, templates


router = APIRouter()


@router.get("/missing", response_class=HTMLResponse)
async def get_missing_persons(
    request: Request,
    search: str | None = None,
    status: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(MissingPerson)
    if status and "All" not in status:
        query = query.where(MissingPerson.status.in_(status))
    if search:
        pattern = f"%{search}%"
        query = query.where(
            MissingPerson.name.like(pattern) | MissingPerson.last_seen_location.like(pattern)
        )
    people = list((await db.execute(
        query.order_by(MissingPerson.created_at.desc())
    )).scalars().all())
    updates = list((await db.execute(
        select(FamilyUpdate).order_by(FamilyUpdate.created_at.desc()).limit(15)
    )).scalars().all())
    return templates.TemplateResponse(
        request=request,
        name="missing_persons.html",
        context={
            "missing_persons": people,
            "family_updates": updates,
            "selected_statuses": status or ["All"],
            "search_query": search or "",
            "total_records": len(people),
            "current_tab": "missing_persons",
        },
    )


@router.post("/missing/report", response_class=RedirectResponse)
async def submit_missing_report(
    name: str = Form(...),
    status: str = Form(...),
    age: int | None = Form(None),
    height: str | None = Form(None),
    condition: str | None = Form(None),
    last_seen_location: str = Form(...),
    photo: UploadFile | None = File(None),
    contact_name: str | None = Form(None),
    contact_phone: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    db.add(MissingPerson(
        name=name,
        status=status,
        age=age,
        height=height,
        condition=condition,
        last_seen_location=last_seen_location,
        photo_url=save_upload(photo, "mp_"),
        contact_name=contact_name,
        contact_phone=contact_phone,
        created_at=utc_now(),
    ))
    await db.commit()
    return RedirectResponse(url="/missing", status_code=303)


@router.post("/missing/update", response_class=RedirectResponse)
async def add_family_update(
    author: str = Form(...),
    message: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    db.add(FamilyUpdate(author=author, message=message, created_at=utc_now()))
    await db.commit()
    return RedirectResponse(url="/missing", status_code=303)
