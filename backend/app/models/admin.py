from pydantic import BaseModel

from app.models.mission import MissionHistoryEntry
from app.models.report import CommunityReportSnapshot
from app.models.safety import SafetyEventResponse


class AdminTerritoryMetric(BaseModel):
    label: str
    value: str
    tone: str = "neutral"
    detail: str | None = None


class AdminPressureZone(BaseModel):
    zone_id: str
    zone_label: str
    overall_score: float
    color: str
    active_boats: int
    inbound_missions: int
    pressure_ratio: float
    pollution_index: int
    legal_status: str
    advisory: str


class AdminSourceHealth(BaseModel):
    source_key: str
    freshness: str
    detail: str
    age_minutes: int | None = None


class AdminOverviewResponse(BaseModel):
    generated_at: str
    admin_email: str
    territorial_metrics: list[AdminTerritoryMetric]
    pressure_zones: list[AdminPressureZone]
    recent_safety_events: list[SafetyEventResponse]
    recent_reports: list[CommunityReportSnapshot]
    recent_missions: list[MissionHistoryEntry]
    source_health: list[AdminSourceHealth]
