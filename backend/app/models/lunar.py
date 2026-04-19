from pydantic import BaseModel


class LunarForecastDay(BaseModel):
    day_label: str
    phase_name: str
    illumination_pct: float
    fishing_rating: int


class LunarResponse(BaseModel):
    phase_name: str
    illumination_pct: float
    moonrise: str
    moonset: str
    best_window: str
    species_guidance: list[str]
    forecast: list[LunarForecastDay]

