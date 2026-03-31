"""Main API router — aggregates all sub-routers."""

from fastapi import APIRouter

from app.api import admin, dashboard, feedback, health, kb, tickets, triage

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(tickets.router)
api_router.include_router(triage.router)
api_router.include_router(feedback.router)
api_router.include_router(kb.router)
api_router.include_router(dashboard.router)
api_router.include_router(admin.router)
