"""Dashboard API — KPI and accuracy metrics."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id
from app.schemas.dashboard import ConfidenceBucket, DashboardKPIs, ModuleAccuracy
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

_svc = DashboardService()


@router.get("/kpis", response_model=DashboardKPIs)
async def get_kpis(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return await _svc.get_kpis(db=db, tenant_id=tenant_id)


@router.get("/module-accuracy", response_model=list[ModuleAccuracy])
async def get_module_accuracy(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return await _svc.get_module_accuracy(db=db, tenant_id=tenant_id)


@router.get("/confidence-distribution", response_model=list[ConfidenceBucket])
async def get_confidence_distribution(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return await _svc.get_confidence_distribution(db=db, tenant_id=tenant_id)
