from pydantic import BaseModel


class MarineWeatherSnapshot(BaseModel):
    timestamp: str
    air_temperature_c: float | None = None
    water_temperature_c: float | None = None
    wind_speed_kmh: float | None = None
    wind_direction_deg: float | None = None
    wave_height_m: float | None = None
    current_speed_kmh: float | None = None
    gust_kmh: float | None = None
    precipitation_mm_per_hour: float | None = None
    condition: str
    fishing_score: int
    advisory: str


class MarineWeatherResponse(BaseModel):
    lat: float
    lon: float
    source: str
    status: str
    is_live: bool
    current: MarineWeatherSnapshot
    forecast: list[MarineWeatherSnapshot]

