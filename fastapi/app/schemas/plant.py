from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from app.schemas.base import GeoJSONGeometry

class PlantBase(BaseModel):
    """Base plant schema"""
    name: str
    geometry: GeoJSONGeometry
    
    @field_validator('geometry')
    @classmethod
    def validate_polygon(cls, v):
        if v.type != "Polygon":
            raise ValueError('Geometry type must be Polygon')
        return v


class PlantCreate(PlantBase):
    """Schema for creating a plant"""
    pass


class PlantUpdate(BaseModel):
    """Schema for updating a plant"""
    name: Optional[str] = None
    geometry: Optional[GeoJSONGeometry] = None
    
    @field_validator('geometry')
    @classmethod
    def validate_polygon(cls, v):
        if v is not None and v.type != "Polygon":
            raise ValueError('Geometry type must be Polygon')
        return v


class Plant(PlantBase):
    """Schema for plant response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class PlantInDB(Plant):
    """Schema for plant in database"""
    pass
