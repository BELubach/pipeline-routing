"""CRUD operations for Plant model"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape, mapping
import json

from app.models.plant import Plant
from app.schemas.plant import PlantCreate, PlantUpdate


def geojson_to_wkt(geojson: dict) -> str:
    """Convert GeoJSON to WKT format"""
    geom = shape(geojson)
    return geom.wkt


def wkt_to_geojson(wkt_element) -> dict:
    """Convert WKT element to GeoJSON"""
    geom = to_shape(wkt_element)
    return mapping(geom)


async def create_plant(db: AsyncSession, plant_in: PlantCreate) -> Plant:
    """Create a new plant"""
    geojson = plant_in.geometry.model_dump()
    wkt = geojson_to_wkt(geojson)
    
    plant = Plant(
        name=plant_in.name,
        geometry=f"SRID=4326;{wkt}"
    )
    
    db.add(plant)
    await db.commit()
    await db.refresh(plant)
    return plant


async def get_plant_by_id(db: AsyncSession, plant_id: int) -> Optional[Plant]:
    """Get plant by ID"""
    result = await db.execute(
        select(Plant).where(Plant.id == plant_id)
    )
    return result.scalar_one_or_none()


async def get_plants(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100
) -> List[Plant]:
    """Get all plants with pagination"""
    result = await db.execute(
        select(Plant).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_plant(
    db: AsyncSession, 
    plant_id: int, 
    plant_in: PlantUpdate
) -> Optional[Plant]:
    """Update a plant"""
    plant = await get_plant_by_id(db, plant_id)
    if not plant:
        return None
    
    update_data = plant_in.model_dump(exclude_unset=True)
    
    # Convert geometry if provided
    if "geometry" in update_data and update_data["geometry"]:
        geojson = update_data["geometry"]
        wkt = geojson_to_wkt(geojson)
        update_data["geometry"] = f"SRID=4326;{wkt}"
    
    for field, value in update_data.items():
        setattr(plant, field, value)
    
    await db.commit()
    await db.refresh(plant)
    return plant


async def delete_plant(db: AsyncSession, plant_id: int) -> bool:
    """Delete a plant"""
    plant = await get_plant_by_id(db, plant_id)
    if not plant:
        return False
    
    await db.delete(plant)
    await db.commit()
    return True
