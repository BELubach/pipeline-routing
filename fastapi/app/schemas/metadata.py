"""
Dataset metadata schemas for proper attribution and licensing
"""

from datetime import date, datetime
from typing import Optional, Any
from pydantic import BaseModel, HttpUrl, Field, ConfigDict


class ResponseMetadata(BaseModel):
    """Metadata included in API responses for attribution and context"""
    
    dataset_id: str = Field(..., description="Dataset identifier")
    dataset_name: str = Field(..., description="Human-readable dataset name")
    source: str = Field(..., description="Data source/provider")
    organization: str = Field(..., description="Organization responsible for the data")
    license: str = Field(..., description="License type")
    attribution: str = Field(..., description="Required attribution text")
    
    # Response context
    record_count: int = Field(..., description="Number of records in this response")
    total_records: Optional[int] = Field(None, description="Total records available (if different from returned)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response generation timestamp")
    filters_applied: Optional[dict[str, Any]] = Field(None, description="Filters applied to this query")
    
    # Additional info links
    dataset_url: Optional[HttpUrl] = Field(None, description="Dataset website")
    documentation_url: Optional[HttpUrl] = Field(None, description="Documentation URL")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "dataset_id": "iggielgn",
            "dataset_name": "IGGIELGN Gas Network Dataset",
            "source": "SciGRID_gas",
            "organization": "Institute of Networked Energy Systems, DLR",
            "license": "ODbL-1.0",
            "attribution": "SciGRID_gas IGGIELGN, DLR",
            "record_count": 150,
            "timestamp": "2026-03-31T12:00:00Z",
            "filters_applied": {"country": "DE"}
        }
    })


class DatasetMetadata(BaseModel):
    """Metadata for a single dataset used in the API"""
    
    id: str = Field(..., description="Unique identifier for the dataset")
    name: str = Field(..., description="Human-readable name of the dataset")
    source: str = Field(..., description="Primary source or data provider")
    organization: str = Field(..., description="Organization responsible for the dataset")
    version: Optional[str] = Field(None, description="Dataset version or release identifier")
    dataset_date: Optional[date] = Field(None, description="Date of dataset release or last update")
    
    # Licensing and attribution
    license: str = Field(..., description="License type (e.g., CC-BY-4.0, ODbL)")
    license_url: Optional[HttpUrl] = Field(None, description="URL to full license text")
    attribution: str = Field(..., description="Required attribution text")
    
    # Additional information
    website: Optional[HttpUrl] = Field(None, description="Official dataset website")
    documentation_url: Optional[HttpUrl] = Field(None, description="Documentation or methodology URL")
    doi: Optional[str] = Field(None, description="Digital Object Identifier (DOI) if available")
    
    # Usage information
    description: Optional[str] = Field(None, description="Brief description of the dataset")
    geographic_coverage: Optional[str] = Field(None, description="Geographic coverage (e.g., 'European Union', 'Global')")
    data_types: Optional[list[str]] = Field(None, description="Types of data provided (e.g., nodes, pipelines, terminals)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "iggielgn",
            "name": "IGGIELGN Gas Network Dataset",
            "source": "SciGRID_gas",
            "organization": "Institute of Networked Energy Systems, DLR",
            "version": "v0.4",
            "dataset_date": "2021-03-15",
            "license": "ODbL-1.0",
            "license_url": "https://opendatacommons.org/licenses/odbl/1.0/",
            "attribution": "SciGRID_gas, Institute of Networked Energy Systems, German Aerospace Center (DLR)",
            "website": "https://www.gas.scigrid.de/",
            "documentation_url": "https://www.gas.scigrid.de/downloads/scigrid_gas_IGGIELGN_2019-10-22.pdf",
            "description": "High-resolution model of the European gas transmission network",
            "geographic_coverage": "European Union",
            "data_types": ["pipelines", "nodes", "border_crossings", "lng_terminals"]
        }
    })


class DatasetResponse(BaseModel):
    """Response containing all dataset metadata"""
    
    datasets: list[DatasetMetadata] = Field(..., description="List of all datasets used in the API")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "datasets": [
                {
                    "id": "iggielgn",
                    "name": "IGGIELGN Gas Network Dataset",
                    "source": "SciGRID_gas",
                    "organization": "Institute of Networked Energy Systems, DLR"
                }
            ]
        }
    })
