from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.chatbot import get_chatbot_response
from app.web import templates

router = APIRouter()

@router.get("/chatbot", response_class=HTMLResponse)
async def get_chatbot_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="chatbot.html",
        context={"current_tab": "chatbot"},
    )

@router.post("/api/chatbot")
async def post_chatbot_message(
    message: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    response = await get_chatbot_response(message, db)
    return {"response": response}
