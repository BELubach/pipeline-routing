"""
Dataset metadata endpoints
Provides information about data sources, attribution, and licensing
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.metadata import DatasetDetailsdata, DatasetListResponse, DatasetMetadata
from app.services.metadata import get_all_datasets, get_active_datasets, get_dataset_metadata

router = APIRouter()


@router.get("", response_model=DatasetListResponse)
async def list_datasets():
    """
    List all datasets available in the API with full attribution and licensing information.
    
    Returns metadata for all datasets including:
    - Data source and organization
    - License and attribution requirements
    - Dataset version and date
    - Documentation URLs
    - Geographic coverage
    """
    datasets = get_all_datasets()
    return DatasetListResponse(datasets=datasets)


@router.get("/active", response_model=DatasetListResponse)
async def list_active_datasets():
    """
    List currently active/implemented datasets.
    
    Returns metadata only for datasets that are actively being used
    in the current API deployment.
    """
    datasets = get_active_datasets()
    return DatasetListResponse(datasets=datasets)


@router.get("/{dataset_id}", response_model=DatasetMetadata)
async def get_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get detailed metadata for a specific dataset by ID.
    
    Available dataset IDs:
    - iggielgn: IGGIELGN Gas Network Dataset (SciGRID_gas)
    - gem_pipelines: Global Energy Monitor Gas Infrastructure Tracker
    """
    metadata = await get_dataset_metadata(db, dataset_id)
    if not metadata:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found in registry"
        )
    return metadata



