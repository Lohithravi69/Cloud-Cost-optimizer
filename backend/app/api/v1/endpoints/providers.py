"""
Cloud provider management endpoints
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.logging import get_logger
from app.services.providers import get_provider_service

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[schemas.CloudProvider])
def read_providers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve cloud providers
    """
    providers = crud.provider.get_multi(db, skip=skip, limit=limit)
    return providers


@router.post("/", response_model=schemas.CloudProvider)
def create_provider(
    *,
    db: Session = Depends(deps.get_db),
    provider_in: schemas.CloudProviderCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new cloud provider connection
    """
    # Validate provider credentials
    provider_service = get_provider_service(provider_in.provider_type)
    if not provider_service.validate_credentials(provider_in.credentials):
        raise HTTPException(
            status_code=400,
            detail="Invalid provider credentials"
        )

    provider = crud.provider.create_with_owner(
        db=db, obj_in=provider_in, owner_id=current_user.id
    )
    logger.info(
        "Provider connection created",
        user_id=current_user.id,
        provider_id=provider.id,
        provider_type=provider.provider_type
    )
    return provider


@router.get("/{provider_id}", response_model=schemas.CloudProvider)
def read_provider(
    *,
    db: Session = Depends(deps.get_db),
    provider_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get provider by ID
    """
    provider = crud.provider.get(db, id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if not crud.provider.is_owner(current_user, provider):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return provider


@router.put("/{provider_id}", response_model=schemas.CloudProvider)
def update_provider(
    *,
    db: Session = Depends(deps.get_db),
    provider_id: int,
    provider_in: schemas.CloudProviderUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a provider
    """
    provider = crud.provider.get(db, id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if not crud.provider.is_owner(current_user, provider):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Validate credentials if they're being updated
    if provider_in.credentials:
        provider_service = get_provider_service(provider.provider_type)
        if not provider_service.validate_credentials(provider_in.credentials):
            raise HTTPException(
                status_code=400,
                detail="Invalid provider credentials"
            )

    provider = crud.provider.update(db, db_obj=provider, obj_in=provider_in)
    logger.info("Provider updated", provider_id=provider_id, user_id=current_user.id)
    return provider


@router.delete("/{provider_id}")
def delete_provider(
    *,
    db: Session = Depends(deps.get_db),
    provider_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a provider
    """
    provider = crud.provider.get(db, id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if not crud.provider.is_owner(current_user, provider):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    crud.provider.remove(db, id=provider_id)
    logger.info("Provider deleted", provider_id=provider_id, user_id=current_user.id)
    return {"message": "Provider deleted successfully"}


@router.post("/{provider_id}/test-connection")
def test_provider_connection(
    *,
    db: Session = Depends(deps.get_db),
    provider_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Test connection to cloud provider
    """
    provider = crud.provider.get(db, id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if not crud.provider.is_owner(current_user, provider):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    provider_service = get_provider_service(provider.provider_type)
    try:
        success = provider_service.test_connection(provider.credentials)
        if success:
            logger.info("Provider connection test successful", provider_id=provider_id)
            return {"status": "success", "message": "Connection successful"}
        else:
            logger.warning("Provider connection test failed", provider_id=provider_id)
            return {"status": "failed", "message": "Connection failed"}
    except Exception as e:
        logger.error("Provider connection test error", provider_id=provider_id, error=str(e))
        return {"status": "error", "message": f"Connection error: {str(e)}"}


@router.post("/{provider_id}/sync-data")
def sync_provider_data(
    *,
    db: Session = Depends(deps.get_db),
    provider_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Manually trigger data sync from cloud provider
    """
    provider = crud.provider.get(db, id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if not crud.provider.is_owner(current_user, provider):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # TODO: Implement data sync logic
    logger.info("Data sync triggered", provider_id=provider_id, user_id=current_user.id)
    return {"message": "Data sync initiated", "provider_id": provider_id}
