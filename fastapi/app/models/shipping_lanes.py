from sqlalchemy import (
    Column, BigInteger, Float, String
)
from geoalchemy2 import Geometry
from app.db.session import Base


class ShippingLane(Base):
    __tablename__ = "shipping_lanes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lane_name = Column(String, nullable=True)
    geom = Column(Geometry("LINESTRING", srid=4326), nullable=False)
    distance_km = Column(Float, nullable=True)

