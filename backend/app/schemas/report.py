"""
Report schemas for cost analysis and insights
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CostReport(BaseModel):
    """
    Cost summary report schema
    """
    title: str
    generated_at: str
    period: Dict[str, Optional[str]]
    provider: Optional[str]
    group_by: str
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]


class AnomalyReport(BaseModel):
    """
    Cost anomaly detection report schema
    """
    title: str
    generated_at: str
    period: Dict[str, Optional[str]]
    provider: Optional[str]
    threshold: float
    anomalies: List[Dict[str, Any]]
    summary: Dict[str, Any]


class OptimizationReport(BaseModel):
    """
    Cost optimization opportunities report schema
    """
    title: str
    generated_at: str
    period: Dict[str, Optional[str]]
    provider: Optional[str]
    opportunities: List[Dict[str, Any]]
    summary: Dict[str, Any]


class CostChartData(BaseModel):
    """
    Cost chart data schema
    """
    labels: List[str]
    datasets: List[Dict[str, Any]]
    period: str
    total_cost: float


class ServiceBreakdown(BaseModel):
    """
    Service cost breakdown schema
    """
    services: List[Dict[str, Any]]
    total_cost: float
    period_days: int


class AlertsSummary(BaseModel):
    """
    Alerts summary schema
    """
    total_alerts: int
    unresolved_alerts: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    recent_alerts: List[Dict[str, Any]]


class OptimizationDashboard(BaseModel):
    """
    Optimization dashboard data schema
    """
    total_opportunities: int
    potential_monthly_savings: float
    implemented_savings: float
    by_category: Dict[str, Dict[str, Any]]
    priority_recommendations: List[Dict[str, Any]]


class DashboardOverview(BaseModel):
    """
    Dashboard overview schema
    """
    total_cost: float
    daily_average: float
    cost_trend: str
    cost_change_percent: float
    provider_breakdown: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]
    optimization_summary: Dict[str, Any]
    last_updated: str
