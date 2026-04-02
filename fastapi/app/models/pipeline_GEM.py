from sqlalchemy import (
    Column, BigInteger, Date, Integer, String, Text, DateTime, Numeric, ARRAY, JSON
)
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.db.session import Base


class GEMPipelineSegment(Base):
    __tablename__ = "gem_pipeline_segments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    project_id = Column(String, index=True, nullable=False)
    pipeline_name = Column(String, nullable=False)
    segment_name = Column(String, nullable=True)
    wiki = Column(Text, nullable=True)

    status = Column(String, nullable=True)
    last_updated = Column(Date, nullable=True)
    fuel = Column(String, nullable=True)

    countries_or_areas = Column(Text, nullable=True)

    owner = Column(Text, nullable=True)
    parent = Column(Text, nullable=True)
    parent_entity_ids = Column(ARRAY(String), nullable=True)

    start_year_1 = Column(Integer, nullable=True)
    start_year_2 = Column(Integer, nullable=True)
    start_year_3 = Column(Integer, nullable=True)
    shelved_year = Column(Integer, nullable=True)
    cancelled_year = Column(Integer, nullable=True)
    stop_year = Column(Integer, nullable=True)

    capacity = Column(Numeric(14, 2), nullable=True)
    capacity_units = Column(String, nullable=True)
    capacity_bcm_y = Column(Numeric(14, 2), nullable=True)
    capacity_boe_d = Column(Numeric(14, 2), nullable=True)

    length_known_km = Column(Numeric(12, 2), nullable=True)
    length_estimate_km = Column(Numeric(12, 2), nullable=True)
    length_merged_km = Column(Numeric(12, 2), nullable=True)

    diameter_raw = Column(String, nullable=True)
    diameter_units = Column(String, nullable=True)

    start_country_or_area = Column(String, nullable=True)
    start_state_province = Column(String, nullable=True)
    start_prefecture_district = Column(String, nullable=True)

    end_location = Column(String, nullable=True)
    end_country_or_area = Column(String, nullable=True)
    end_state_province = Column(String, nullable=True)
    end_prefecture_district = Column(String, nullable=True)

    route_accuracy = Column(String, nullable=True)
    route_type = Column(String, nullable=True)

    geom = Column(Geometry("MULTILINESTRING", srid=4326), nullable=False)

    raw_properties = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())