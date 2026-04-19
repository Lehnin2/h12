from pydantic import BaseModel, Field, field_validator


VALID_REPORT_TYPES = {
    "catch",
    "pollution",
    "hazard",
    "illegal_activity",
    "current",
}


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())


class CommunityReportCreate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    report_type: str
    severity: int = Field(default=3, ge=1, le=5)
    species: str | None = None
    note: str | None = Field(default=None, max_length=280)

    @field_validator("report_type")
    @classmethod
    def _validate_report_type(cls, value: str) -> str:
        normalized = _clean_text(value).lower()
        if normalized not in VALID_REPORT_TYPES:
            raise ValueError(
                f"report_type must be one of: {', '.join(sorted(VALID_REPORT_TYPES))}"
            )
        return normalized

    @field_validator("species", "note")
    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _clean_text(value).lower()
        return cleaned or None


class CommunityReportSnapshot(BaseModel):
    id: str
    user_id: str
    reporter_name: str
    lat: float
    lon: float
    report_type: str
    severity: int
    species: str | None = None
    note: str | None = None
    recorded_at: str
    zone_id: str | None = None
    zone_label: str | None = None


class ZoneReportSummary(BaseModel):
    zone_id: str
    zone_label: str
    total_reports: int
    catch_reports: int
    pollution_reports: int
    hazard_reports: int
    illegal_activity_reports: int
    current_reports: int
    productivity_signal: float
    risk_signal: float
    advisory: str | None = None


class CommunityReportFeedResponse(BaseModel):
    recent_reports: list[CommunityReportSnapshot]
    zone_summaries: list[ZoneReportSummary]

