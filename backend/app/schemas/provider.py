"""
Cloud provider schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CloudProviderBase(BaseModel):
    """
    Base cloud provider schema
    """
    name: str
    provider_type: str  # aws, azure, gcp
    account_id: str
    region: Optional[str] = None
    is_active: bool = True


class CloudProviderCreate(CloudProviderBase):
    """
    Schema for creating a new cloud provider connection
    """
    credentials: dict  # Encrypted credentials storage


class CloudProviderUpdate(BaseModel):
    """
    Schema for updating cloud provider connection
    """
    name: Optional[str] = None
    region: Optional[str] = None
    is_active: Optional[bool] = None
    credentials: Optional[dict] = None


class CloudProvider(CloudProviderBase):
    """
    Full cloud provider schema
    """
    id: int
    created_at: datetime
    updated_at: datetime
    last_sync: Optional[datetime] = None
    sync_status: str = "never"

    class Config:
        from_attributes = True


class CloudProviderTest(BaseModel):
    """
    Schema for testing cloud provider connection
    """
    success: bool
    message: str
    details: Optional[dict] = None


class SyncResult(BaseModel):
    """
    Schema for sync operation results
    """
    provider: str
    status: str  # success, failed, partial
    records_processed: int
    message: str
    errors: Optional[list] = None
