from pydantic import BaseModel


class Port(BaseModel):
    id: str
    name: str
    short_name: str
    lat: float
    lon: float
    risk_bias: float


class GeoPoint(BaseModel):
    lat: float
    lon: float

