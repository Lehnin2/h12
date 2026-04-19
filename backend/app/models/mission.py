from pydantic import BaseModel

from app.models.lunar import LunarResponse
from app.models.regulation import RegulationAssessmentResponse
from app.models.routing import RouteResponse
from app.models.safety import SafetyStatusResponse
from app.models.satellite import SatelliteObservationResponse
from app.models.weather import MarineWeatherResponse
from app.models.zone import HeatmapResponse, RecommendationResponse


class MissionDepartureDecision(BaseModel):
    status: str
    score: int
    summary: str
    reasons: list[str]
    actions: list[str]


class MissionSourceFreshness(BaseModel):
    source_key: str
    source_name: str
    freshness: str
    age_minutes: int | None = None
    observed_at: str | None = None
    is_live: bool = False
    detail: str


class MissionHistoryEntry(BaseModel):
    id: str
    requested_at: str
    departure_port: str
    selected_species: str
    recommended_zone_id: str
    recommended_zone_label: str
    departure_status: str
    mission_score: int


class MissionHistoryResponse(BaseModel):
    entries: list[MissionHistoryEntry]


class MissionBriefingResponse(BaseModel):
    departure_port: str
    selected_species: str
    heatmap: HeatmapResponse
    recommendation: RecommendationResponse
    regulation: RegulationAssessmentResponse
    route: RouteResponse
    satellite: SatelliteObservationResponse
    weather: MarineWeatherResponse
    lunar: LunarResponse
    safety: SafetyStatusResponse
    departure_decision: MissionDepartureDecision
    source_freshness: list[MissionSourceFreshness]
