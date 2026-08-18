"""RESPOND-ER FastAPI application assembly.

Domain behavior lives in routers and services; this module only wires the app.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import verify_database_revision
from app.routers import dashboard, donations, emergencies, people, recovery, resources, shelters, chatbot
from app.web import STATIC_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    await verify_database_revision()
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="RESPOND-ER Command Center", lifespan=lifespan)
    application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    application.include_router(dashboard.router)
    application.include_router(emergencies.router)
    application.include_router(people.router)
    application.include_router(donations.router)
    application.include_router(shelters.router)
    application.include_router(resources.router)
    application.include_router(recovery.router)
    application.include_router(chatbot.router)
    return application


app = create_app()

# Compatibility for scripts that call the startup check directly.
startup = verify_database_revision
