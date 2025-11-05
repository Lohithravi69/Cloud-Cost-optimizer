"""
Dashboard endpoints for real-time cost monitoring and visualization
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/overview", response_model=schemas.DashboardOverview)
def get_dashboard_overview(
    db: Session = Depends(deps.get_db),
    days: int = Query(30, description="Number of days to look back"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get dashboard overview with key metrics
    """
    logger.info("Fetching dashboard overview", user_id=current_user.id, days=days)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get cost data
    cost_data = crud.cost_data.get_multi(
        db=db,
        start_date=start_date,
        end_date=end_date,
        limit=5000
    )

    # Calculate metrics
    total_cost = sum(float(record.cost_amount or 0) for record in cost_data)
    daily_average = total_cost / days if days > 0 else 0

    # Get provider breakdown
    provider_costs = {}
    for record in cost_data:
        provider = record.provider or 'Unknown'
        cost = float(record.cost_amount or 0)
        provider_costs[provider] = provider_costs.get(provider, 0) + cost

    # Get recent alerts (placeholder - would come from alerts table)
    recent_alerts = [
        {
            "id": "alert_1",
            "type": "budget_threshold",
            "message": "Monthly budget threshold exceeded",
            "severity": "high",
            "timestamp": (end_date - timedelta(hours=2)).isoformat()
        },
        {
            "id": "alert_2",
            "type": "anomaly",
            "message": "Unusual cost spike detected in EC2",
            "severity": "medium",
            "timestamp": (end_date - timedelta(hours=5)).isoformat()
        }
    ]

    # Get optimization summary (placeholder)
    optimization_summary = {
        "total_opportunities": 12,
        "potential_savings": 850.50,
        "implemented_savings": 320.75
    }

    overview_data = {
        "total_cost": round(total_cost, 2),
        "daily_average": round(daily_average, 2),
        "cost_trend": "increasing",  # Would be calculated from historical data
        "cost_change_percent": 8.5,  # Would be calculated
        "provider_breakdown": [
            {"provider": provider, "cost": round(cost, 2), "percentage": round(cost/total_cost*100, 1) if total_cost > 0 else 0}
            for provider, cost in provider_costs.items()
        ],
        "recent_alerts": recent_alerts,
        "optimization_summary": optimization_summary,
        "last_updated": end_date.isoformat()
    }

    return overview_data


@router.get("/cost-chart", response_model=schemas.CostChartData)
def get_cost_chart_data(
    db: Session = Depends(deps.get_db),
    provider: str = Query(None, description="Cloud provider filter"),
    period: str = Query("daily", description="Chart period: hourly, daily, weekly, monthly"),
    days: int = Query(30, description="Number of days to show"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get cost data formatted for charts
    """
    logger.info(
        "Fetching cost chart data",
        user_id=current_user.id,
        provider=provider,
        period=period,
        days=days
    )

    if period not in ["hourly", "daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid period")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get cost data
    cost_data = crud.cost_data.get_multi(
        db=db,
        provider=provider,
        start_date=start_date,
        end_date=end_date,
        limit=5000
    )

    # Process data for charting
    import pandas as pd

    if cost_data:
        df = pd.DataFrame([{
            'timestamp': record.start_date or record.end_date,
            'cost': float(record.cost_amount or 0),
            'provider': record.provider or 'Unknown',
            'service': record.service or 'Unknown'
        } for record in cost_data])

        # Group by time period
        if period == "monthly":
            df['period'] = df['timestamp'].dt.to_period('M').astype(str)
        elif period == "weekly":
            df['period'] = df['timestamp'].dt.to_period('W').astype(str)
        elif period == "daily":
            df['period'] = df['timestamp'].dt.date.astype(str)
        else:  # hourly
            df['period'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:00')

        grouped = df.groupby('period').agg({'cost': 'sum'}).reset_index()
        chart_data = grouped.to_dict('records')
    else:
        chart_data = []

    return {
        "labels": [item['period'] for item in chart_data],
        "datasets": [{
            "label": f"Cost ({provider or 'All Providers'})",
            "data": [item['cost'] for item in chart_data],
            "borderColor": "rgb(75, 192, 192)",
            "backgroundColor": "rgba(75, 192, 192, 0.2)",
        }],
        "period": period,
        "total_cost": sum(item['cost'] for item in chart_data)
    }


@router.get("/service-breakdown", response_model=schemas.ServiceBreakdown)
def get_service_breakdown(
    db: Session = Depends(deps.get_db),
    provider: str = Query(None, description="Cloud provider filter"),
    days: int = Query(30, description="Number of days to analyze"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get cost breakdown by service
    """
    logger.info(
        "Fetching service breakdown",
        user_id=current_user.id,
        provider=provider,
        days=days
    )

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    cost_data = crud.cost_data.get_multi(
        db=db,
        provider=provider,
        start_date=start_date,
        end_date=end_date,
        limit=5000
    )

    # Group by service
    service_costs = {}
    total_cost = 0

    for record in cost_data:
        service = record.service or 'Unknown'
        cost = float(record.cost_amount or 0)
        service_costs[service] = service_costs.get(service, 0) + cost
        total_cost += cost

    # Convert to list with percentages
    breakdown = [
        {
            "service": service,
            "cost": round(cost, 2),
            "percentage": round(cost/total_cost*100, 1) if total_cost > 0 else 0
        }
        for service, cost in service_costs.items()
    ]

    # Sort by cost descending
    breakdown.sort(key=lambda x: x['cost'], reverse=True)

    return {
        "services": breakdown,
        "total_cost": round(total_cost, 2),
        "period_days": days
    }


@router.get("/alerts-summary", response_model=schemas.AlertsSummary)
def get_alerts_summary(
    db: Session = Depends(deps.get_db),
    days: int = Query(7, description="Number of days to look back"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get summary of recent alerts and notifications
    """
    logger.info("Fetching alerts summary", user_id=current_user.id, days=days)

    # TODO: Implement actual alerts querying
    # For now, return placeholder data
    alerts_summary = {
        "total_alerts": 8,
        "unresolved_alerts": 3,
        "by_severity": {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 2
        },
        "by_type": {
            "budget_threshold": 3,
            "anomaly": 2,
            "resource_idle": 2,
            "security": 1
        },
        "recent_alerts": [
            {
                "id": "alert_1",
                "type": "budget_threshold",
                "message": "Monthly budget 85% utilized",
                "severity": "medium",
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "resolved": False
            },
            {
                "id": "alert_2",
                "type": "anomaly",
                "message": "Cost spike in Lambda functions",
                "severity": "high",
                "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                "resolved": False
            }
        ]
    }

    return alerts_summary


@router.get("/optimization-dashboard", response_model=schemas.OptimizationDashboard)
def get_optimization_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get optimization dashboard data
    """
    logger.info("Fetching optimization dashboard", user_id=current_user.id)

    # TODO: Integrate with optimization engine
    # For now, return placeholder data
    optimization_data = {
        "total_opportunities": 15,
        "potential_monthly_savings": 1250.75,
        "implemented_savings": 450.25,
        "by_category": {
            "idle_resources": {"count": 5, "savings": 380.50},
            "underutilized": {"count": 4, "savings": 295.25},
            "unused_storage": {"count": 3, "savings": 125.00},
            "inefficient_instances": {"count": 3, "savings": 450.00}
        },
        "priority_recommendations": [
            {
                "id": "rec_1",
                "title": "Terminate 3 idle EC2 instances",
                "description": "Instances unused for 45+ days",
                "potential_savings": 180.00,
                "difficulty": "low",
                "impact": "high"
            },
            {
                "id": "rec_2",
                "title": "Downsize RDS instance",
                "description": "CPU utilization consistently below 20%",
                "potential_savings": 95.50,
                "difficulty": "medium",
                "impact": "medium"
            }
        ]
    }

    return optimization_data
