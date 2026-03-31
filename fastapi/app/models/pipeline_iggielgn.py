from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, Numeric, 
    Boolean, ARRAY, CheckConstraint, ForeignKey, Index
)
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.db.session import Base




class BorderNode(Base):
    """
    Represents a pipeline entry/exit or border crossing node.
    Derived from GeoJSON point features in the dataset.
    """
    __tablename__ = "border_nodes"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    IGGIELGN_id = Column(String, nullable=False)           # e.g., "INET_BP_0"
    name = Column(String, nullable=True)           # e.g., "Almeria_[208]"
    geom = Column(Geometry("POINT", srid=4326), nullable=False)  # PostGIS geometry
    country_code = Column(String, nullable=False)   # Country where node is located
    from_country = Column(String, nullable=False)   # Source country for pipeline segment
    to_country = Column(String, nullable=False)     # Destination country for pipeline segment
    from_TSO = Column(String, nullable=True)        # Source Transmission System Operator
    to_TSO = Column(String, nullable=True)          # Destination TSO

 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return  f"<BorderNode(id={self.id}, name={self.name}, country={self.country_code})>"


class GenericNode(Base):
    """
    A generic node table for any point features that don't fit other categories.
    This can be used for nodes that are not yet classified or for future data imports.
    """
    __tablename__ = "generic_nodes"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    IGGIELGN_id = Column(String, nullable=False)           # e.g., "INET_BP_0"
    name = Column(Text, nullable=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    country_code = Column(String(2))  # ISO 3166-1 alpha-2 country code

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<GenericNode(id={self.id}, name={self.name})>"


class PipelineSegment(Base):
    """
    Represents a pipeline segment connecting two nodes.
    Used to map the network topology and for routing calculations. 
    Will be an edge in the pgRouting graph.
    """

    __tablename__ = "pipeline_segments"
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    IGGIELGN_id = Column(String, nullable=True)           # e.g., "INET_PL_273_EE_0_Seg_0_Seg_0"
    from_node_id = Column(String, ForeignKey("generic_nodes.id"), nullable=True)
    to_node_id = Column(String, ForeignKey("generic_nodes.id"), nullable=True)

    country_code_from = Column(String(2))  # ISO 3166-1 alpha-2 code for source country
    country_code_to = Column(String(2))    # ISO 3166-1 alpha-2 code for destination country

    is_H_gas = Column(Boolean, nullable=False, default=True)  # Whether the segment carries high-calorific gas
    length_km = Column(Numeric(10, 2), nullable=False)  # Length of segment in kilometers
    diameter_mm = Column(Numeric(10, 2), nullable=True)  
    max_cap_M_m3_per_d = Column(Numeric(10, 2), nullable=True)  # Max capacity in million cubic meters per day
    max_pressure_bar = Column(Numeric(10, 2), nullable=True)  # Max operating pressure in bar

    geom = Column(Geometry("LINESTRING", srid=4326), nullable=False)  # PostGIS geometry for the pipeline route

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<PipelineSegment(id={self.id}, from={self.from_node_id}, to={self.to_node_id})>"



class LngTerminal(Base):
    """
    Represents an LNG terminal, which can be a source or sink in the network.
    Derived from point features in the dataset with specific attributes.
    """
    __tablename__ = "lng_terminals"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    IGGIELGN_id = Column(String, nullable=False)                            # e.g., "INET_LNG_0"
    name = Column(String, nullable=True)                                    # e.g., "Zeebrugge_[209]"
    geom = Column(Geometry("POINT", srid=4326), nullable=False)             # PostGIS geometry
    country_code = Column(String, nullable=False)                           # Country where terminal is located
    max_cap_store2pipe_M_m3_per_d = Column(Numeric(10, 2), nullable=True)   # Terminal capacity
    start_year = Column(Integer, nullable=True)                             # Year terminal started operation
    from_TSO = Column(String, nullable=True)                                # TSO that supplies the terminal
    to_TSO = Column(String, nullable=True)                                  # TSO that receives from the terminal

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<LngTerminal(id={self.id}, name={self.name}, country={self.country_code})>"