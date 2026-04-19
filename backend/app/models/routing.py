from pydantic import BaseModel

from app.models.shared import GeoPoint


class RouteLeg(BaseModel):
    label: str
    point: GeoPoint
    safety_state: str


class RouteResponse(BaseModel):
    departure_port: str
    target_zone_id: str
    direct_distance_km: float
    optimized_distance_km: float
    estimated_duration_h: float
    estimated_fuel_l: float
    savings_l: float
    min_depth_m: float
    max_depth_m: float
    route_risk_level: str
    weather_risk_level: str
    route_readiness: str
    sea_state_summary: str
    path: list[RouteLeg]
    safety_notes: list[str]
