from fastapi import APIRouter, Query

from app.models.bathymetry import BathymetryDepthResponse
from app.services.bathymetry_service import bathymetry_service

router = APIRouter()


@router.get("/depth", response_model=BathymetryDepthResponse)
def get_depth(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
) -> BathymetryDepthResponse:
    return bathymetry_service.depth_at(lat, lon)

