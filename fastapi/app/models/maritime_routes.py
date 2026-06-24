from sqlalchemy import (
    ARRAY, Column, BigInteger, Float, Text
)
from geoalchemy2 import Geometry
from app.db.session import Base


class MaritimeRoutes(Base):
    __tablename__ = "maritime_routes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=True)
    pass_ = Column("pass", Text, nullable=True)
    source = Column(BigInteger, nullable=True)
    target = Column(BigInteger, nullable=True)



class MaritimeRoutesVertices(Base):
    __tablename__ = "maritime_routes_vertices"

    id = Column(BigInteger, primary_key=True)
    in_edges = Column(ARRAY(BigInteger), nullable=True)
    out_edges = Column(ARRAY(BigInteger), nullable=True)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)