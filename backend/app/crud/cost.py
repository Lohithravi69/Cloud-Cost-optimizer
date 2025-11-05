"""
CRUD operations for cost data
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app import models, schemas


class CRUDCostData:
    """
    CRUD operations for cost data
    """

    def get(self, db: Session, id: int) -> Optional[models.CostData]:
        return db.query(models.CostData).filter(models.CostData.id == id).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        provider: Optional[str] = None,
        service: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[models.CostData]:
        query = db.query(models.CostData)

        if provider:
            query = query.filter(models.CostData.provider == provider)
        if service:
            query = query.filter(models.CostData.service == service)
        if start_date:
            query = query.filter(models.CostData.timestamp >= start_date)
        if end_date:
            query = query.filter(models.CostData.timestamp <= end_date)

        return query.offset(skip).limit(limit).all()

    def get_summary(
        self,
        db: Session,
        *,
        provider: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> schemas.CostSummary:
        query = db.query(models.CostData)

        if provider:
            query = query.filter(models.CostData.provider == provider)
        if start_date:
            query = query.filter(models.CostData.timestamp >= start_date)
        if end_date:
            query = query.filter(models.CostData.timestamp <= end_date)

        # Calculate summary statistics
        total_cost = query.with_entities(db.func.sum(models.CostData.cost)).scalar() or 0
        avg_cost = query.with_entities(db.func.avg(models.CostData.cost)).scalar() or 0
        count = query.count()

        return schemas.CostSummary(
            total_cost=total_cost,
            average_cost=avg_cost,
            record_count=count,
            provider=provider,
            start_date=start_date,
            end_date=end_date,
        )

    def get_trends(
        self,
        db: Session,
        *,
        provider: Optional[str] = None,
        period: str = "daily",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[schemas.CostTrend]:
        # This is a simplified implementation
        # In a real application, you'd use proper date aggregation
        query = db.query(models.CostData)

        if provider:
            query = query.filter(models.CostData.provider == provider)
        if start_date:
            query = query.filter(models.CostData.timestamp >= start_date)
        if end_date:
            query = query.filter(models.CostData.timestamp <= end_date)

        # Group by date and calculate totals
        # This is a placeholder - actual implementation would depend on your database
        results = query.all()

        # Mock trend data for now
        trends = []
        for i in range(7):  # Last 7 days
            trends.append(
                schemas.CostTrend(
                    date=datetime.now().date(),
                    total_cost=100.0 + i * 10,
                    provider=provider or "all",
                )
            )

        return trends

    def create(self, db: Session, *, obj_in: schemas.CostDataCreate) -> models.CostData:
        db_obj = models.CostData(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: models.CostData, obj_in: schemas.CostDataUpdate
    ) -> models.CostData:
        update_data = obj_in.dict(exclude_unset=True)
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> models.CostData:
        obj = db.query(models.CostData).get(id)
        db.delete(obj)
        db.commit()
        return obj


cost_data = CRUDCostData()
