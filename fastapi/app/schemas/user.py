from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    CLUSTER_ADMIN = "CLUSTER_ADMIN"
    COMPANY_OWNER = "COMPANY_OWNER"
    UTILITY_PROVIDER = "UTILITY_PROVIDER"


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = UserRole.COMPANY_OWNER
    is_active: Optional[bool] = True
    is_superuser: bool = False


class UserCreate(UserBase):
    email: EmailStr
    password: str
    role: UserRole = UserRole.COMPANY_OWNER


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str
