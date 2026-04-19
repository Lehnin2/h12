from pydantic import BaseModel, Field


class ZoneSeed(BaseModel):
    id: str
    label: str
    center_lat: float
    center_lon: float
    depth_m: float
    pollution_risk: float
    legal_status: str
    fleet_load: float
    chlorophyll: float
    wave_height: float
    current_speed: float
    recommended_species: list[str] = Field(default_factory=list)


class ZoneCard(BaseModel):
    id: str
    label: str
    center_lat: float
    center_lon: float
    depth_m: float
    slope_deg: float = 0.0
    legal_status: str
    pollution_risk: float
    pollution_index: int = 0
    pollution_source: str | None = None
    pollution_data_live: bool = False
    fleet_load: float
    fish_score: float
    overall_score: float
    confidence: float
    color: str
    satellite_source: str = "copernicus_fallback_seeded"
    satellite_live: bool = False
    sst_c: float | None = None
    chlorophyll_mg_m3: float | None = None
    salinity_psu: float | None = None
    turbidity_fnu: float | None = None
    satellite_current_speed_kmh: float | None = None
    satellite_productivity_index: int = 0
    marine_condition: str = "calm"
    marine_fishing_score: int = 0
    weather_source: str = "seeded_fallback"
    weather_live: bool = False
    active_boats: int = 0
    recommended_boats: int = 0
    saturation_ratio: float = 0.0
    predicted_pressure: float = 0.0
    community_reports: int = 0
    recommended_species: list[str]
    key_reason: str


class HeatmapResponse(BaseModel):
    departure_port: str
    selected_species: str
    zones: list[ZoneCard]
    legend: dict[str, str]
    pollution_plume_origin: str


class RecommendationResponse(BaseModel):
    departure_port: str
    selected_species: str
    best_zone: ZoneCard
    alternatives: list[ZoneCard]
    recommendation_status: str = "ACTIONABLE"
    minimum_safe_score: float = 58.0
    viable_zones_count: int = 0
    advisory: str = ""
    rationale: list[str]
