from pydantic import BaseModel


class BathymetryDepthResponse(BaseModel):
    lat: float
    lon: float
    elevation_m: float
    depth_m: float
    slope_deg: float
    status: str
    source: str
