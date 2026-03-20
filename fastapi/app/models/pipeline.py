from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, Numeric, 
    Boolean, ARRAY, CheckConstraint, ForeignKey, Index
)
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.db.session import Base


class PipelineNode(Base):
    """
    Pipeline network nodes: compressor stations, border crossings, 
    hubs, LNG terminals, intersections.
    These are the vertices in the pgRouting graph.
    """
    __tablename__ = "pipeline_nodes"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(Text, nullable=False)
    node_type = Column(
        Text, 
        nullable=False,
        info={
            'check_constraint': CheckConstraint(
                "node_type IN ('compressor_station', 'border_crossing', 'hub', "
                "'lng_terminal', 'storage', 'production', 'intersection')",
                name="check_node_type"
            )
        }
    )
    country = Column(String(2))  # ISO 3166-1 alpha-2
    geom = Column(Geometry('POINT', srid=4326), nullable=False)
    
    # Operational state
    status = Column(
        Text, 
        nullable=False, 
        default='operating',
        server_default='operating',
        info={
            'check_constraint': CheckConstraint(
                "status IN ('operating', 'construction', 'planned', 'decommissioned')",
                name="check_node_status"
            )
        }
    )
    
    # For hubs: is this a tradeable point?
    is_trading_hub = Column(Boolean, default=False, server_default='false')
    hub_code = Column(Text)  # e.g. 'TTF', 'NCG', 'NBP'
    
    # For LNG terminals
    lng_capacity_bcm = Column(Numeric(8, 2))  # send-out capacity bcm/year
    lng_type = Column(
        Text,
        info={
            'check_constraint': CheckConstraint(
                "lng_type IN ('import', 'export', 'both') OR lng_type IS NULL",
                name="check_lng_type"
            )
        }
    )
    
    # Source data
    gem_id = Column(Text)  # Global Energy Monitor ID
    source_name = Column(Text)  # original name in source dataset
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<PipelineNode(id={self.id}, name={self.name}, type={self.node_type})>"


class PipelineEdge(Base):
    """
    Pipeline network edges (segments): physical pipeline segments between two nodes.
    Each row represents one pipeline segment with routing costs for pgRouting.
    """
    __tablename__ = "pipeline_edges"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    
    # pgRouting graph columns (required names)
    source = Column(BigInteger, ForeignKey('pipeline_nodes.id', ondelete='CASCADE'))
    target = Column(BigInteger, ForeignKey('pipeline_nodes.id', ondelete='CASCADE'))
    
    # Geometry: the actual pipeline route
    geom = Column(Geometry('LINESTRING', srid=4326))
    
    # Identity
    pipeline_name = Column(Text)  # e.g. 'Langeled', 'OPAL', 'Medgaz'
    pipeline_code = Column(Text)  # short code, e.g. 'LANG', 'OPAL'
    operator = Column(Text)
    country_codes = Column(ARRAY(Text))  # countries this segment passes through
    
    # Physical properties
    diameter_mm = Column(Integer)  # nominal diameter
    pressure_bar = Column(Integer)  # max operating pressure
    capacity_mcm_d = Column(Numeric(10, 2))  # capacity in million cubic metres per day
    year_built = Column(Integer)
    length_km = Column(Numeric(10, 3))  # computed or provided
    
    # Status
    status = Column(
        Text,
        nullable=False,
        default='operating',
        server_default='operating',
        info={
            'check_constraint': CheckConstraint(
                "status IN ('operating', 'construction', 'planned', 'decommissioned', 'suspended')",
                name="check_edge_status"
            )
        }
    )
    
    # Cost columns for pgRouting optimization
    # Three cost columns for different optimization objectives:
    # - cost_distance_km: pure geographic distance
    # - cost_tariff_eur_mwh: transmission tariff (€/MWh)  
    # - cost_composite: best estimate combining both
    cost_distance_km = Column(Numeric(10, 3))
    cost_tariff_eur_mwh = Column(Numeric(8, 4))
    cost_composite = Column(Numeric(10, 4))
    
    # Reverse costs (pipelines are mostly bidirectional, but not always)
    reverse_cost_distance_km = Column(Numeric(10, 3))
    reverse_cost_tariff_eur_mwh = Column(Numeric(8, 4))
    reverse_cost_composite = Column(Numeric(10, 4))
    
    # Tariff metadata
    tariff_type = Column(
        Text,
        info={
            'check_constraint': CheckConstraint(
                "tariff_type IN ('distance_based', 'fixed_entry', 'negotiated', "
                "'regulated', 'estimated') OR tariff_type IS NULL",
                name="check_tariff_type"
            )
        }
    )
    tariff_source = Column(Text)  # e.g. 'ENTSOG 2024', 'estimated'
    tariff_year = Column(Integer)
    
    # Source data
    gem_id = Column(Text)
    source_name = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<PipelineEdge(id={self.id}, name={self.pipeline_name}, source={self.source}, target={self.target})>"


class TariffRule(Base):
    """
    Lookup table for tariff estimation when real data is missing.
    Used to populate cost_composite via the update script.
    """
    __tablename__ = "tariff_rules"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rule_name = Column(Text, nullable=False)
    country = Column(String(2))  # NULL = global fallback
    tariff_type = Column(Text)
    eur_per_mwh_per_100km = Column(Numeric(6, 4))  # distance-based component
    fixed_entry_eur_mwh = Column(Numeric(6, 4))  # fixed entry point fee
    source = Column(Text)
    valid_from = Column(DateTime(timezone=True))
    valid_to = Column(DateTime(timezone=True))
    notes = Column(Text)
    
    def __repr__(self):
        return f"<TariffRule(id={self.id}, name={self.rule_name}, country={self.country})>"
