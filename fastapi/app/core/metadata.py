"""
Dataset metadata registry
Contains attribution and licensing information for all datasets used in the API
"""

from datetime import date
from typing import Any
from app.schemas.metadata import DatasetMetadata, ResponseMetadata


# IGGIELGN Dataset (SciGRID_gas)
IGGIELGN_METADATA = DatasetMetadata(
    id="iggielgn",
    name="IGGIELGN - Integrated Gas Grid Infrastructure European Long-Distance Gas Network",
    source="SciGRID_gas",
    organization="Institute of Networked Energy Systems, German Aerospace Center (DLR)",
    version="v0.4",
    dataset_date=date(2021, 3, 15),
    
    # Licensing (ODbL requires attribution and share-alike)
    license="ODbL-1.0 (Open Database License)",
    license_url="https://opendatacommons.org/licenses/odbl/1.0/",
    attribution=(
        "SciGRID_gas IGGIELGN, Institute of Networked Energy Systems, "
        "German Aerospace Center (DLR). Based on OpenStreetMap data © OpenStreetMap contributors."
    ),
    
    # Additional information
    website="https://www.gas.scigrid.de/",
    documentation_url="https://www.gas.scigrid.de/downloads.html",
    doi="10.25532/OPARA-42",
    
    description=(
        "High-resolution model of the European gas transmission network. "
        "Includes gas pipelines, border crossing points, LNG terminals, "
        "and compressor stations across Europe."
    ),
    geographic_coverage="European Union and neighboring countries",
    data_types=["pipelines", "nodes", "border_crossings", "lng_terminals", "compressor_stations"]
)


# GEM (Global Energy Monitor) Dataset - Prepared for future use
GEM_METADATA = DatasetMetadata(
    id="gem_pipelines",
    name="GEM Global Gas Infrastructure Tracker (GGIT)",
    source="Global Energy Monitor",
    organization="Global Energy Monitor",
    version="2025-11",
    dataset_date=date(2025, 11, 1),
    
    # Licensing
    license="CC-BY-4.0 (Creative Commons Attribution 4.0 International)",
    license_url="https://creativecommons.org/licenses/by/4.0/",
    attribution=(
        "Global Energy Monitor, Global Gas Infrastructure Tracker (GGIT), "
        "https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/"
    ),
    
    # Additional information
    website="https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/",
    documentation_url="https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/methodology/",
    
    description=(
        "Global dataset tracking gas pipelines, LNG terminals, and other gas infrastructure worldwide. "
        "Includes planned, under construction, and operational facilities."
    ),
    geographic_coverage="Global",
    data_types=["pipelines", "lng_terminals", "gas_plants"]
)


# Registry of all available datasets
DATASET_REGISTRY = {
    "iggielgn": IGGIELGN_METADATA,
    "gem_pipelines": GEM_METADATA,
}


def get_dataset_metadata(dataset_id: str) -> DatasetMetadata | None:
    """Retrieve metadata for a specific dataset by ID"""
    return DATASET_REGISTRY.get(dataset_id)


def get_all_datasets() -> list[DatasetMetadata]:
    """Retrieve metadata for all registered datasets"""
    return list(DATASET_REGISTRY.values())


def get_active_datasets() -> list[DatasetMetadata]:
    """
    Retrieve metadata for currently active/implemented datasets
    Modify this function as you add/remove datasets
    """
    # Currently only IGGIELGN is implemented
    return [IGGIELGN_METADATA]


def create_response_metadata(
    dataset_id: str,
    record_count: int,
    filters_applied: dict[str, Any] | None = None,
    total_records: int | None = None
) -> ResponseMetadata:
    """
    Create response metadata from dataset registry
    
    Args:
        dataset_id: ID of the dataset (e.g., 'iggielgn')
        record_count: Number of records in the response
        filters_applied: Dictionary of filters applied to the query
        total_records: Total records available (if limited by pagination/filters)
    
    Returns:
        ResponseMetadata object ready to include in API response
    """
    dataset = get_dataset_metadata(dataset_id)
    if not dataset:
        # Fallback if dataset not found
        return ResponseMetadata(
            dataset_id=dataset_id,
            dataset_name="Unknown Dataset",
            source="Unknown",
            organization="Unknown",
            license="Unknown",
            attribution="Unknown",
            record_count=record_count,
            total_records=total_records,
            filters_applied=filters_applied
        )
    
    return ResponseMetadata(
        dataset_id=dataset.id,
        dataset_name=dataset.name,
        source=dataset.source,
        organization=dataset.organization,
        license=dataset.license,
        attribution=dataset.attribution,
        record_count=record_count,
        total_records=total_records,
        filters_applied=filters_applied,
        dataset_url=dataset.website,
        documentation_url=dataset.documentation_url
    )
