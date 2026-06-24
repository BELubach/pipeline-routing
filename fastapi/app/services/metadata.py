"""
Dataset metadata registry
Contains attribution and licensing information for all datasets used in the API
"""

from datetime import date
from typing import Any

from sqlalchemy import column, func, select, table
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maritime_routes import MaritimeRoutes
from app.models.pipeline_GEM import GEMPipelineSegment
from app.models.pipeline_iggielgn import BorderNode, GenericNode, LngTerminal, PipelineSegment
from app.schemas.metadata import (
    DatasetComponentDerivation,
    DatasetComponentStorage,
    DatasetDetailsdata,
    DatasetMetadata,
    DatasetComponent,
    ResponseMetadata,
)


# IGGIELGN Dataset (SciGRID_gas)
IGGIELGN_METADATA = DatasetDetailsdata(
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
    data_types=["pipelines", "nodes", "border_crossings",
                "lng_terminals", "compressor_stations"]
)


# GEM (Global Energy Monitor) Dataset - Prepared for future use
GEM_METADATA = DatasetDetailsdata(
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
    data_types=["pipeline_segments", "derived_nodes"]
)


MARITIME_ROUTES_METADATA = DatasetDetailsdata(
    id="maritime_routes",
    name="Maritime Routes",
    source="Internal maritime routing import",
    organization="cluster_infra_sim",
    version=None,
    dataset_date=None,
    license="Unknown",
    license_url=None,
    attribution="Internal maritime routing import used for pathfinding.",
    website=None,
    documentation_url=None,
    doi=None,
    description="Maritime route network used for sea routing and pathfinding.",
    geographic_coverage="Global",
    data_types=["maritime_routes", "maritime_routes_vertices"],
)


# Registry of all available datasets
DATASET_REGISTRY = {
    "iggielgn": IGGIELGN_METADATA,
    "gem_pipelines": GEM_METADATA,
    "maritime_routes": MARITIME_ROUTES_METADATA,
}


MARITIME_ROUTES_VERTICES = table("maritime_routes_vertices", column("id"))


def get_dataset_details(dataset_id: str) -> DatasetDetailsdata | None:
    """Retrieve metadata for a specific dataset by ID"""
    return DATASET_REGISTRY.get(dataset_id)


def get_all_datasets() -> list[DatasetDetailsdata]:
    """Retrieve metadata for all registered datasets"""
    return list(DATASET_REGISTRY.values())


def get_active_datasets() -> list[DatasetDetailsdata]:
    """
    Retrieve metadata for currently active/implemented datasets
    Modify this function as you add/remove datasets
    """
    return [IGGIELGN_METADATA, GEM_METADATA, MARITIME_ROUTES_METADATA]


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
    dataset = get_dataset_details(dataset_id)
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


async def _count_rows(db: AsyncSession, count_from: Any) -> int:
    """Count rows for a mapped table or SQLAlchemy table-like selectable."""

    result = await db.execute(select(func.count()).select_from(count_from))
    count = result.scalar_one()
    return int(count or 0)


async def get_dataset_metadata(db: AsyncSession, dataset_id: str) -> DatasetMetadata | None:
    """
    Retrieve metadata for a specific dataset by ID, formatted for API response

    Args:
        dataset_id: ID of the dataset (e.g., 'iggielgn')

    Returns:
        DatasetMetadata object with all relevant fields for API response
    """
    dataset = get_dataset_details(dataset_id)
    if not dataset:
        return None

    if dataset_id == "iggielgn":
        structure_definition = {
            "has_nodes": True,
            "has_edges": True,
            "primary_network_type": "gas_pipeline",
            "components": [
                {
                    "key": "border_nodes",
                    "label": "Border Nodes",
                    "kind": "node",
                    "table_name": "border_nodes",
                    "count_from": BorderNode.__table__,
                    "storage_source": "stored",
                    "description": "Pipeline entry/exit and border crossing nodes.",
                },
                {
                    "key": "generic_nodes",
                    "label": "Generic Nodes",
                    "kind": "node",
                    "table_name": "generic_nodes",
                    "count_from": GenericNode.__table__,
                    "storage_source": "stored",
                    "description": "General point nodes in the IGGIELGN network.",
                },
                {
                    "key": "lng_terminals",
                    "label": "LNG Terminals",
                    "kind": "node",
                    "table_name": "lng_terminals",
                    "count_from": LngTerminal.__table__,
                    "storage_source": "stored",
                    "description": "LNG terminal locations.",
                },
                {
                    "key": "pipeline_segments",
                    "label": "Pipeline Segments",
                    "kind": "edge",
                    "table_name": "pipeline_segments",
                    "count_from": PipelineSegment.__table__,
                    "storage_source": "stored",
                    "description": "Network edges connecting IGGIELGN nodes.",
                },
            ],
        }
    elif dataset_id == "gem_pipelines":
        structure_definition = {
            "has_nodes": False,
            "has_edges": True,
            "primary_network_type": "gas_pipeline",
            "components": [
                {
                    "key": "pipeline_segments",
                    "label": "Pipeline Segments",
                    "kind": "edge",
                    "table_name": "gem_pipeline_segments",
                    "count_from": GEMPipelineSegment.__table__,
                    "storage_source": "stored",
                    "description": "Stored GEM pipeline geometries and attributes.",
                },
                {
                    "key": "derived_nodes",
                    "label": "Derived Nodes",
                    "kind": "node",
                    "table_name": None,
                    "count_from": None,
                    "storage_source": "derived",
                    "storage_status": "planned",
                    "description": "Future node layer derived from pipeline segment endpoints.",
                    "derivation": {
                        "derived_from": ["pipeline_segments"],
                        "method": "segment endpoints",
                        "derived_at": None,
                    },
                },
            ],
        }
    elif dataset_id == "maritime_routes":
        structure_definition = {
            "has_nodes": True,
            "has_edges": True,
            "primary_network_type": "maritime_route",
            "components": [
                {
                    "key": "maritime_routes",
                    "label": "Maritime Routes",
                    "kind": "edge",
                    "table_name": "maritime_routes",
                    "count_from": MaritimeRoutes.__table__,
                    "storage_source": "stored",
                    "description": "Route edge geometries used for maritime pathfinding.",
                },
                {
                    "key": "maritime_routes_vertices",
                    "label": "Maritime Route Vertices",
                    "kind": "node",
                    "table_name": "maritime_routes_vertices",
                    "count_from": MARITIME_ROUTES_VERTICES,
                    "storage_source": "derived",
                    "description": "Routing graph vertices extracted from maritime route edges.",
                    "derivation": {
                        "derived_from": ["maritime_routes"],
                        "method": "pgr_extractVertices",
                        "derived_at": None,
                    },
                },
            ],
        }
    else:
        structure_definition = None

    if not structure_definition:
        return DatasetMetadata(
            dataset_id=dataset_id,
            has_nodes=False,
            has_edges=False,
            primary_network_type="unknown",
            components=[],
        )

    components: list[DatasetComponent] = []
    for component_definition in structure_definition["components"]:
        count_from = component_definition.get("count_from")
        record_count = await _count_rows(db, count_from) if count_from is not None else 0

        derivation_definition = component_definition.get("derivation")
        derivation = (
            DatasetComponentDerivation(**derivation_definition)
            if derivation_definition is not None
            else None
        )

        components.append(
            DatasetComponent(
                key=component_definition["key"],
                label=component_definition["label"],
                kind=component_definition["kind"],
                record_count=record_count,
                storage=DatasetComponentStorage(
                    table=component_definition.get("table_name"),
                    source=component_definition["storage_source"],
                    status=component_definition.get("storage_status"),
                ),
                derivation=derivation,
                description=component_definition.get("description"),
            )
        )

    return DatasetMetadata(
        id=dataset_id,
        name=dataset.name,
        description=dataset.description,
        has_nodes=structure_definition["has_nodes"],
        has_edges=structure_definition["has_edges"],
        primary_network_type=structure_definition["primary_network_type"],
        components=components,
    )
