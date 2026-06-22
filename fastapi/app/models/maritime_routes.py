from sqlalchemy import (
    Column, BigInteger, Text
)
from geoalchemy2 import Geometry
from app.db.session import Base


class MaritimeRoutes(Base):
    __tablename__ = "maritime_routes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=True)
    pass_ = Column("pass", Text, nullable=True)