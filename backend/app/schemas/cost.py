"""
Pydantic schemas for cost-related data models
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CostDataBase(BaseModel):
    """Base schema for cost data"""
    provider: str = Field(..., description="Cloud provider (aws, azure, gcp)")
    service: str = Field(..., description="Cloud service name")
    resource_id: str = Field(..., description="Unique resource identifier")
    resource_type: str = Field(..., description="Type of resource")
    region: str = Field(..., description="Cloud region")
    cost_amount: Decimal = Field(..., description="Cost amount in USD")
    cost_currency: str = Field(default="USD", description="Cost currency")
    usage_quantity: Optional[Decimal] = Field(None, description="Usage quantity")
    usage_unit: Optional[str] = Field(None, description="Usage unit")
    tags: Dict[str, str] = Field(default_factory=dict, description="Resource tags")
    timestamp: datetime = Field(..., description="Cost timestamp")


class CostDataCreate(CostDataBase):
    """Schema for creating cost data"""
    pass


class CostDataUpdate(CostDataBase):
    """Schema for updating cost data"""
    pass


class CostData(CostDataBase):
    """Schema for cost data response"""
    id: int = Field(..., description="Database ID")

    class Config:
        from_attributes = True


class CostSummary(BaseModel):
    """Schema for cost summary statistics"""
    total_cost: Decimal = Field(..., description="Total cost across all providers")
    provider_breakdown: Dict[str, Decimal] = Field(..., description="Cost by provider")
    service_breakdown: Dict[str, Decimal] = Field(..., description="Cost by service")
    region_breakdown: Dict[str, Decimal] = Field(..., description="Cost by region")
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")
    cost_trend: str = Field(..., description="Cost trend (increasing, decreasing, stable)")


class CostTrend(BaseModel):
    """Schema for cost trend data"""
    period: str = Field(..., description="Time period")
    cost: Decimal = Field(..., description="Total cost for period")
    provider_costs: Dict[str, Decimal] = Field(..., description="Cost by provider for period")
    change_percentage: Optional[Decimal] = Field(None, description="Percentage change from previous period")


class SyncResult(BaseModel):
    """Schema for data synchronization results"""
    provider: str = Field(..., description="Cloud provider synced")
    status: str = Field(..., description="Sync status (success, partial, failed)")
    records_processed: int = Field(..., description="Number of records processed")
    message: str = Field(..., description="Sync result message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Sync timestamp")
