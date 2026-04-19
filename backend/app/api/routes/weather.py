from fastapi import APIRouter, Query

from app.models.weather import MarineWeatherResponse
from app.services.weather_service import weather_service

router = APIRouter()


@router.get("/point", response_model=MarineWeatherResponse)
def weather_point(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    hours: int = Query(default=8, ge=1, le=24),
) -> MarineWeatherResponse:
    return weather_service.get_point_forecast(lat, lon, hours)


@router.get("/port/{port_id}", response_model=MarineWeatherResponse)
def weather_port(
    port_id: str,
    hours: int = Query(default=8, ge=1, le=24),
) -> MarineWeatherResponse:
    return weather_service.get_port_forecast(port_id, hours)

