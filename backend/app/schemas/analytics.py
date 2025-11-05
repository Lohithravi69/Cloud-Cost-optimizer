"""
Pydantic schemas for analytics-related data models
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CostTrendAnalysis(BaseModel):
    """Schema for cost trend analysis results"""
    trend: str = Field(..., description="Trend direction (increasing, decreasing, stable)")
    change_percentage: float = Field(..., description="Percentage change in costs")
    forecast: List[Dict[str, float]] = Field(default_factory=list, description="Cost forecast data")
    insights: List[str] = Field(default_factory=list, description="Analysis insights")
    data_points: int = Field(..., description="Number of data points analyzed")
    period: str = Field(..., description="Analysis period")


class CostAnomaly(BaseModel):
    """Schema for cost anomaly detection results"""
    date: str = Field(..., description="Date of anomaly")
    cost_amount: float = Field(..., description="Anomalous cost amount")
    anomaly_score: float = Field(..., description="Anomaly score/severity")
    method: str = Field(..., description="Detection method used")
    severity: str = Field(..., description="Anomaly severity (low, medium, high, critical)")


class ForecastData(BaseModel):
    """Schema for individual forecast data point"""
    date: str = Field(..., description="Forecast date")
    predicted_cost: float = Field(..., description="Predicted cost amount")
    lower_bound: float = Field(..., description="Lower confidence bound")
    upper_bound: float = Field(..., description="Upper confidence bound")


class CostForecast(BaseModel):
    """Schema for cost forecast results"""
    forecast: List[ForecastData] = Field(default_factory=list, description="Forecast data points")
    confidence_intervals: List[float] = Field(default_factory=list, description="Confidence interval values")
    accuracy_metrics: Dict[str, float] = Field(default_factory=dict, description="Forecast accuracy metrics")
    insights: List[str] = Field(default_factory=list, description="Forecast insights")


class CostBreakdownItem(BaseModel):
    """Schema for individual cost breakdown item"""
    category: str = Field(..., description="Breakdown category")
    cost: float = Field(..., description="Cost amount for category")
    percentage: float = Field(..., description="Percentage of total cost")


class CostBreakdown(BaseModel):
    """Schema for cost breakdown analysis results"""
    breakdown: Dict[str, float] = Field(default_factory=dict, description="Cost breakdown by category")
    top_contributors: List[CostBreakdownItem] = Field(default_factory=list, description="Top cost contributors")
    total_cost: float = Field(..., description="Total cost across all categories")
    insights: List[str] = Field(default_factory=list, description="Breakdown insights")


class OptimizationRecommendation(BaseModel):
    """Schema for optimization recommendations"""
    resource_id: str = Field(..., description="Resource identifier")
    resource_type: str = Field(..., description="Type of resource")
    provider: str = Field(..., description="Cloud provider")
    current_cost: float = Field(..., description="Current monthly cost")
    potential_savings: float = Field(..., description="Potential monthly savings")
    savings_percentage: float = Field(..., description="Percentage savings")
    recommendation_type: str = Field(..., description="Type of recommendation")
    priority: str = Field(..., description="Recommendation priority (low, medium, high, critical)")
    description: str = Field(..., description="Detailed recommendation description")
    implementation_steps: List[str] = Field(default_factory=list, description="Steps to implement recommendation")
    risk_level: str = Field(..., description="Implementation risk level")


class OptimizationSummary(BaseModel):
    """Schema for optimization analysis summary"""
    total_current_cost: float = Field(..., description="Total current monthly cost")
    total_potential_savings: float = Field(..., description="Total potential monthly savings")
    savings_percentage: float = Field(..., description="Overall savings percentage")
    recommendations_count: int = Field(..., description="Number of recommendations")
    high_priority_count: int = Field(..., description="Number of high-priority recommendations")
    recommendations: List[OptimizationRecommendation] = Field(default_factory=list, description="List of recommendations")
    insights: List[str] = Field(default_factory=list, description="Optimization insights")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last analysis timestamp")
