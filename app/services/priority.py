"""Emergency triage execution and dispatch queue ranking."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.services.triage import analyze_emergency_priority
from app.database import SessionLocal
from app.models import EmergencyRequest
from app.services.vulnerability import (
    AI_PRIORITY_SCORES,
    apply_vulnerability_scores,
    final_priority_score_for,
)


async def rerank_pending_requests(db: AsyncSession, ai_weight: float = 0.60, hvi_weight: float = 0.40) -> list[EmergencyRequest]:
    result = await db.execute(
        select(EmergencyRequest)
        .options(selectinload(EmergencyRequest.vulnerability_assessment))
        .where(EmergencyRequest.status != "Completed")
    )
    requests = list(result.scalars().all())
    for request in requests:
        apply_vulnerability_scores(request, request.ai_priority, ai_weight, hvi_weight)
    requests.sort(
        key=lambda request: (
            AI_PRIORITY_SCORES.get(request.priority_override, -1)
            if request.priority_override
            else final_priority_score_for(request),
            request.created_at or datetime.min,
        ),
        reverse=True,
    )
    for rank, request in enumerate(requests, start=1):
        request.priority_rank = rank
    return requests


async def run_ai_triage(request_id: int) -> None:
    async with SessionLocal() as db:
        request = await db.get(EmergencyRequest, request_id)
        if not request:
            return
        triage = await analyze_emergency_priority(
            description=request.description,
            people_affected=request.people_affected,
            request_type=request.request_type,
        )
        apply_vulnerability_scores(request, triage["priority"])
        request.description = f"AI Dispatch: {triage['reasoning']}\n\n{request.description}"
        await rerank_pending_requests(db)
        await db.commit()
