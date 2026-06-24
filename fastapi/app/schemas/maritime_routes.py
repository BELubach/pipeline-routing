from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Dict, Any
from datetime import datetime


class MaritimeRoute(BaseModel):
    """GeoJSON Geometry schema"""
    type: str
    coordinates: list