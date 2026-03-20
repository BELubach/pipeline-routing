"""Plant endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

from app.db.session import get_db
from app.schemas.plant import Plant, PlantCreate, PlantUpdate, GeoJSONGeometry
from app.schemas.user import User
from app.crud import crud_plant
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


def convert_geometry_to_geojson(plant):
    """Convert plant geometry to GeoJSON for response"""
    if plant.geometry:
        geom = to_shape(plant.geometry)
        plant.geometry = GeoJSONGeometry(
            type=geom.geom_type,
            coordinates=list(geom.exterior.coords)
        )
    return plant


@router.post("", response_model=Plant, status_code=status.HTTP_201_CREATED)
async def create_plant(
    plant_in: PlantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new plant"""
    plant = await crud_plant.create_plant(db, plant_in=plant_in)
    
    # Convert geometry to GeoJSON for response
    if plant.geometry:
        geom = to_shape(plant.geometry)
        geojson = mapping(geom)
        plant.geometry = geojson
    
    return plant


@router.get("", response_model=List[Plant])
async def list_plants(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all plants"""
    plants = await crud_plant.get_plants(db, skip=skip, limit=limit)
    
    # Convert geometries to GeoJSON
    for plant in plants:
        if plant.geometry:
            geom = to_shape(plant.geometry)
            geojson = mapping(geom)
            plant.geometry = geojson
    
    return plants


@router.get("/{plant_id}", response_model=Plant)
async def get_plant(
    plant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific plant by ID"""
    plant = await crud_plant.get_plant_by_id(db, plant_id=plant_id)
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found"
        )
    
    # Convert geometry to GeoJSON
    if plant.geometry:
        geom = to_shape(plant.geometry)
        geojson = mapping(geom)
        plant.geometry = geojson
    
    return plant


@router.put("/{plant_id}", response_model=Plant)
async def update_plant(
    plant_id: int,
    plant_in: PlantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a plant"""
    plant = await crud_plant.update_plant(db, plant_id=plant_id, plant_in=plant_in)
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found"
        )
    
    # Convert geometry to GeoJSON
    if plant.geometry:
        geom = to_shape(plant.geometry)
        geojson = mapping(geom)
        plant.geometry = geojson
    
    return plant


@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plant(
    plant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a plant"""
    success = await crud_plant.delete_plant(db, plant_id=plant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found"
        )
    return None
