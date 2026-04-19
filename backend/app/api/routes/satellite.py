from fastapi import APIRouter, Query

from app.models.satellite import SatelliteObservationResponse, SatelliteZoneResponse
from app.services.satellite_service import satellite_service

router = APIRouter()


@router.get("/point", response_model=SatelliteObservationResponse)
def satellite_point(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
) -> SatelliteObservationResponse:
    return satellite_service.get_point_observation(lat, lon)


@router.get("/zone/{zone_id}", response_model=SatelliteZoneResponse)
def satellite_zone(zone_id: str) -> SatelliteZoneResponse:
    return satellite_service.get_zone_observation(zone_id)

