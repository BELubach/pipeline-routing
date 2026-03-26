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

    id = Column(String, primary_key=True)           # e.g., "INET_BP_0"
    name = Column(String, nullable=False)           # e.g., "Almeria_[208]"
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

    id = Column(String, primary_key=True)           # e.g., "INET_BP_0"
    name = Column(Text, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    country_code = Column(String(2))  # ISO 3166-1 alpha-2 country code

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<GenericNode(id={self.id}, name={self.name})>"