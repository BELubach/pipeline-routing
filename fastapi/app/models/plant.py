from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.db.session import Base


class Plant(Base):
    """Plant model with location polygon"""
    __tablename__ = "plants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Plant(id={self.id}, name={self.name})>"
