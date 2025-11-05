"""
Cost data models
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.db.base_class import Base


class CostData(Base):
    """
    Cost data model for storing cloud cost information
    """
    __tablename__ = "cost_data"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False, index=True)  # aws, azure, gcp
    service = Column(String(100), nullable=False, index=True)  # EC2, S3, etc.
    resource_id = Column(String(255), nullable=True)
    resource_type = Column(String(100), nullable=True)
    region = Column(String(50), nullable=True)
    cost = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    timestamp = Column(DateTime, nullable=False, index=True)
    tags = Column(Text, nullable=True)  # JSON string of tags
    account_id = Column(String(100), nullable=True)
    project_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CostData(id={self.id}, provider={self.provider}, service={self.service}, cost={self.cost})>"
