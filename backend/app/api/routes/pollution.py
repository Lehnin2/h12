from fastapi import APIRouter, Query

from app.models.pollution import (
    PollutionObservationResponse,
    PollutionOverviewResponse,
    PollutionZoneResponse,
)
from app.services.pollution_service import pollution_service

router = APIRouter()


@router.get("/point", response_model=PollutionObservationResponse)
def pollution_point(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
) -> PollutionObservationResponse:
    return pollution_service.get_point_assessment(lat, lon)


@router.get("/zone/{zone_id}", response_model=PollutionZoneResponse)
def pollution_zone(zone_id: str) -> PollutionZoneResponse:
    return pollution_service.get_zone_assessment(zone_id)


@router.get("/overview", response_model=PollutionOverviewResponse)
def pollution_overview(
    within_hours: int = Query(default=48, ge=1, le=336),
) -> PollutionOverviewResponse:
    return pollution_service.overview(within_hours)

