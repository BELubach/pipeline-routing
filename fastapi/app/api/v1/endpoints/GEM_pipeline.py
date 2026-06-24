"""
GEM gas pipeline API
FastAPI router for Global Energy Monitor gas pipeline segments

Data source:
- GEM Global Gas Infrastructure Tracker (GGIT)
  See /api/v1/dataset/datasets/gem_pipelines for full attribution
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.metadata import create_response_metadata
from app.db.session import get_db
from app.models.pipeline_GEM import GEMPipelineSegment
from app.schemas.pipeline import GEMSegmentsResponse, GEMPipelinesResponse, GEMRouteSegment, GEMPipelineDTO

router = APIRouter()


def _to_float(value: object) -> float | None:
    return float(value) if value is not None else None


def _resolve_length_km(segment: GEMPipelineSegment) -> float | None:
    if segment.length_merged_km is not None:
        return float(segment.length_merged_km)
    if segment.length_known_km is not None:
        return float(segment.length_known_km)
    if segment.length_estimate_km is not None:
        return float(segment.length_estimate_km)
    return None


@router.get("/pipelines", response_model=GEMPipelinesResponse)
async def get_pipeline_segments(
        country: str | None = Query(
            None, description="Filter segments by country or area on either end"
        ),
        status: str | None = Query(
            None, description="Filter segments by project status"
        ),
        limit: int | None = Query(
            None, description="Limit number of records returned (default: all)"
        ),
        db: AsyncSession = Depends(get_db),
):
    """
    List GEM pipeline segments with optional filters.

    Data source: GEM Global Gas Infrastructure Tracker (GGIT)
    See /api/v1/dataset/datasets/gem_pipelines for attribution
    """

    statement = (
        select(
            GEMPipelineSegment,
        )
        .order_by(GEMPipelineSegment.id)
    )

    if country:
        statement = statement.where(
            or_(
                GEMPipelineSegment.start_country_or_area == country,
                GEMPipelineSegment.end_country_or_area == country,
                GEMPipelineSegment.countries_or_areas.ilike(f"%{country}%"),
            )
        )

    if status:
        statement = statement.where(GEMPipelineSegment.status == status)

    if limit is not None:
        statement = statement.limit(limit)

    result = await db.execute(statement)
    rows = result.scalars().all()

    segments = [
        GEMPipelineDTO(
            id=segment.id,
            length_km=_resolve_length_km(segment),
            project_id=segment.project_id,
            pipeline_name=segment.pipeline_name,
            segment_name=segment.segment_name,
            wiki=segment.wiki,
            status=segment.status,
            last_updated=segment.last_updated,
            fuel=segment.fuel,
            countries_or_areas=segment.countries_or_areas,
            owner=segment.owner,
            parent=segment.parent,
            parent_entity_ids=segment.parent_entity_ids,
            start_year_1=segment.start_year_1,
            start_year_2=segment.start_year_2,
            start_year_3=segment.start_year_3,
            shelved_year=segment.shelved_year,
            cancelled_year=segment.cancelled_year,
            stop_year=segment.stop_year,
            capacity=_to_float(segment.capacity),
            capacity_units=segment.capacity_units,
            capacity_bcm_y=_to_float(segment.capacity_bcm_y),
            capacity_boe_d=_to_float(segment.capacity_boe_d),
            length_known_km=_to_float(segment.length_known_km),
            length_estimate_km=_to_float(segment.length_estimate_km),
            length_merged_km=_to_float(segment.length_merged_km),
            diameter_raw=segment.diameter_raw,
            diameter_units=segment.diameter_units,
            start_country_or_area=segment.start_country_or_area,
            start_state_province=segment.start_state_province,
            start_prefecture_district=segment.start_prefecture_district,
            end_location=segment.end_location,
            end_country_or_area=segment.end_country_or_area,
            end_state_province=segment.end_state_province,
            end_prefecture_district=segment.end_prefecture_district,
            route_accuracy=segment.route_accuracy,
            route_type=segment.route_type,
            raw_properties=segment.raw_properties,
        )
        for segment in rows
    ]

    filters = {}
    if country:
        filters["country"] = country
    if status:
        filters["status"] = status

    metadata = create_response_metadata(
        dataset_id="gem_pipelines",
        record_count=len(segments),
        total_records=limit if limit is not None and len(
            segments) == limit else None,
        filters_applied=filters if filters else None,
    )

    return GEMPipelinesResponse(data=segments, metadata=metadata)


@router.get("/segments", response_model=GEMSegmentsResponse)
async def get_pipeline_segments(
        limit: int | None = Query(
            None, description="Limit number of records returned (default: all)"
        ),
        db: AsyncSession = Depends(get_db),
):
    """
    List GEM pipeline segments with optional filters.

    Data source: GEM Global Gas Infrastructure Tracker (GGIT)
    See /api/v1/dataset/datasets/gem_pipelines for attribution
    """

    statement = (
        select(
            GEMPipelineSegment,
            func.ST_AsGeoJSON(GEMPipelineSegment.geom).label("geometry"),
        )
        .order_by(GEMPipelineSegment.id)
    )

    if limit is not None:
        statement = statement.limit(limit)

    result = await db.execute(statement)
    rows = result.all()

    segments = [
        GEMRouteSegment(
            id=segment.id,
            length_km=segment.length_estimate_km,
            pipeline_name=segment.pipeline_name,
            geometry=json.loads(geometry) if geometry else None,
        )
        for segment, geometry in rows
    ]

    metadata = create_response_metadata(
        dataset_id="gem_pipelines",
        record_count=len(segments),
        total_records=limit if limit is not None and len(
            segments) == limit else None,
    )

    return GEMSegmentsResponse(data=segments, metadata=metadata)
