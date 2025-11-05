"""
Cost data management endpoints
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[schemas.CostData])
def read_cost_data(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    provider: Optional[str] = Query(None, description="Cloud provider filter"),
    service: Optional[str] = Query(None, description="Service filter"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> List[schemas.CostData]:
    """
    Retrieve cost data with optional filters
    """
    # logger.info(
    #     "Fetching cost data",
    #     # user_id=current_user.id,
    #     filters={
    #         "provider": provider,
    #         "service": service,
    #         "start_date": start_date,
    #         "end_date": end_date,
    #     },
    # )

    # For now, return empty list as we don't have database setup yet
    return []


@router.get("/summary", response_model=schemas.CostSummary)
def read_cost_summary(
    db: Session = Depends(deps.get_db),
    provider: Optional[str] = Query(None, description="Cloud provider filter"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.CostSummary:
    """
    Get cost summary statistics
    """
    # logger.info("Fetching cost summary", user_id=current_user.id)

    # For now, return placeholder summary
    from decimal import Decimal
    return schemas.CostSummary(
        total_cost=Decimal("0.0"),
        provider_breakdown={},
        service_breakdown={},
        region_breakdown={},
        period_start=datetime.utcnow(),
        period_end=datetime.utcnow(),
        cost_trend="stable"
    )


@router.get("/trends", response_model=List[schemas.CostTrend])
def read_cost_trends(
    db: Session = Depends(deps.get_db),
    provider: Optional[str] = Query(None, description="Cloud provider filter"),
    period: str = Query("daily", description="Aggregation period: daily, weekly, monthly"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> List[schemas.CostTrend]:
    """
    Get cost trends over time
    """
    # logger.info("Fetching cost trends", user_id=current_user.id, period=period)

    if period not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid period. Must be daily, weekly, or monthly")

    # For now, return empty list
    return []


@router.post("/sync", response_model=schemas.SyncResult)
async def sync_cost_data(
    *,
    db: Session = Depends(deps.get_db),
    provider: str = Query(..., description="Cloud provider to sync"),
    start_date: Optional[datetime] = Query(None, description="Start date for sync"),
    end_date: Optional[datetime] = Query(None, description="End date for sync"),
    # current_user: models.User = Depends(deps.get_current_superuser),
) -> schemas.SyncResult:
    """
    Trigger manual sync of cost data from cloud provider
    """
    logger.info("Starting cost data sync", provider=provider)

    try:
        from app.services.data_acquisition import data_acquisition_service

        # Sync data for the specified provider
        if provider.lower() == 'all':
            sync_result = await data_acquisition_service.sync_all_providers(
                start_date=start_date,
                end_date=end_date
            )
            result = schemas.SyncResult(
                provider="all",
                status=sync_result['status'],
                records_processed=sync_result['total_records_processed'],
                message=f"Multi-provider sync completed: {sync_result['total_records_processed']} records processed"
            )
        else:
            # Sync single provider
            sync_result = await data_acquisition_service.sync_all_providers(
                start_date=start_date,
                end_date=end_date,
                providers=[provider]
            )
            provider_result = sync_result['provider_results'].get(provider, {})
            result = schemas.SyncResult(
                provider=provider,
                status=provider_result.get('status', 'error'),
                records_processed=provider_result.get('records_processed', 0),
                message=provider_result.get('error', 'Sync completed successfully')
            )

        logger.info("Cost data sync completed", result=result.dict())
        return result

    except Exception as e:
        logger.error("Cost data sync failed", error=str(e))
        return schemas.SyncResult(
            provider=provider,
            status="error",
            records_processed=0,
            message=f"Sync failed: {str(e)}"
        )
