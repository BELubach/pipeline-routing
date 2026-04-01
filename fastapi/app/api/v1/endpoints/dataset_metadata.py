"""
Dataset metadata endpoints
Provides information about data sources, attribution, and licensing
"""

from fastapi import APIRouter
from app.schemas.metadata import DatasetMetadata, DatasetResponse
from app.core.metadata import get_all_datasets, get_active_datasets, get_dataset_metadata

router = APIRouter()


@router.get("/datasets", response_model=DatasetResponse)
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
    return DatasetResponse(datasets=datasets)


@router.get("/datasets/active", response_model=DatasetResponse)
async def list_active_datasets():
    """
    List currently active/implemented datasets.
    
    Returns metadata only for datasets that are actively being used
    in the current API deployment.
    """
    datasets = get_active_datasets()
    return DatasetResponse(datasets=datasets)


@router.get("/datasets/{dataset_id}", response_model=DatasetMetadata)
async def get_dataset(dataset_id: str):
    """
    Get detailed metadata for a specific dataset by ID.
    
    Available dataset IDs:
    - iggielgn: IGGIELGN Gas Network Dataset (SciGRID_gas)
    - gem_pipelines: Global Energy Monitor Gas Infrastructure Tracker
    """
    metadata = get_dataset_metadata(dataset_id)
    if not metadata:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found in registry"
        )
    return metadata
