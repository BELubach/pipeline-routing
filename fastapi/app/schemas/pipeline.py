from pydantic import BaseModel, EmailStr
from typing import Optional

from sqlalchemy import BigInteger


class Node(BaseModel):
    id: BigInteger
    IGGIELGN_id: Optional[str] = None
    lat: float
    lon: float

class BorderNodeDTO(Node):
    
    name: str
    country_code: str
    from_country: str
    to_country: str
    from_TSO: Optional[str] = None
    to_TSO: Optional[str] = None

class GenericNodeDTO(Node):
    name: Optional[str] = None
    country_code: Optional[str] = None