"""Admin API — tenant config and model version management."""

import logging

import yaml
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_config import TenantConfig, load_tenant_config
from app.dependencies import get_db, get_tenant_config, get_tenant_id
from app.models.model_version import ModelVersion

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/tenant/config")
async def get_tenant_config_endpoint(
    tenant_config: TenantConfig = Depends(get_tenant_config),
):
    """Return current tenant configuration as JSON."""
    return tenant_config.model_dump()


@router.put("/tenant/config")
async def update_tenant_config(
    config: dict,
    tenant_id: str = Depends(get_tenant_id),
):
    """Validate and persist updated tenant config, then clear the cache."""
    try:
        validated = TenantConfig.model_validate(config)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid config: {exc}")

    if validated.tenant_id != tenant_id:
        raise HTTPException(
            status_code=400,
            detail="tenant_id in config must match X-Tenant-Id header",
        )

    from pathlib import Path
    config_path = Path(__file__).parent.parent.parent / "config" / f"{tenant_id}.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Clear cached config so next request reloads from disk
    load_tenant_config.cache_clear()

    return {"status": "updated", "tenant_id": tenant_id}


@router.get("/models/versions")
async def list_model_versions(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """List all model versions for the tenant."""
    result = await db.execute(
        select(ModelVersion)
        .where(ModelVersion.tenant_id == tenant_id)
        .order_by(ModelVersion.trained_at.desc())
    )
    versions = result.scalars().all()
    return [
        {
            "id": v.id,
            "model_type": v.model_type,
            "version": v.version,
            "training_samples": v.training_samples,
            "holdout_accuracy": v.holdout_accuracy,
            "is_active": v.is_active,
            "trained_at": v.trained_at.isoformat() if v.trained_at else None,
        }
        for v in versions
    ]
