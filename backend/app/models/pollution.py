from pydantic import BaseModel


class PollutionSourceSnapshot(BaseModel):
    id: str
    name: str
    source_type: str
    lat: float
    lon: float
    base_severity: float
    status: str
    notes: str | None = None


class PollutionObservationResponse(BaseModel):
    lat: float
    lon: float
    source: str
    status: str
    is_live: bool
    observed_at: str
    nearest_source_id: str | None = None
    nearest_source_name: str | None = None
    risk_score: float
    contamination_index: int
    plume_direction_deg: float | None = None
    plume_radius_km: float | None = None
    spread_speed_kmh: float | None = None
    advisory: str


class PollutionPlumeSnapshot(BaseModel):
    source_id: str
    source_name: str
    center_lat: float
    center_lon: float
    observed_at: str
    plume_direction_deg: float
    plume_radius_km: float
    spread_speed_kmh: float
    core_risk: float
    geometry_hint_json: str


class PollutionZoneResponse(BaseModel):
    zone_id: str
    zone_label: str
    observation: PollutionObservationResponse


class PollutionOverviewResponse(BaseModel):
    sources: list[PollutionSourceSnapshot]
    recent_plumes: list[PollutionPlumeSnapshot]

