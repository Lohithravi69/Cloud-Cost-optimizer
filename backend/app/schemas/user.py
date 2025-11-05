"""
Pydantic schemas for user-related data models
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User full name")
    is_active: bool = Field(default=True, description="Whether user is active")
    is_superuser: bool = Field(default=False, description="Whether user is superuser")
    role: str = Field(default="user", description="User role (admin, finance, it_manager, developer)")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(UserBase):
    """Schema for updating user data"""
    password: Optional[str] = Field(None, min_length=8, description="User password")


class UserInDBBase(UserBase):
    """Base schema for user data from database"""
    id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class User(UserInDBBase):
    """Schema for user response (without sensitive data)"""
    pass


class UserInDB(UserInDBBase):
    """Schema for user data in database (with hashed password)"""
    hashed_password: str = Field(..., description="Hashed password")


class Token(BaseModel):
    """Schema for authentication token"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Schema for token payload data"""
    email: Optional[str] = None
    user_id: Optional[int] = None
