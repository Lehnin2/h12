from pydantic import BaseModel, Field, field_validator


def _normalize_note(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned or None


class SafetyCheckInCreate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    note: str | None = Field(default=None, max_length=220)
    battery_level_pct: int | None = Field(default=None, ge=0, le=100)
    sync_mode: str = Field(default="offline_cache", min_length=3, max_length=32)

    @field_validator("note", "sync_mode")
    @classmethod
    def _clean_text(cls, value: str | None) -> str | None:
        return _normalize_note(value)


class SafetySosCreate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    message: str | None = Field(default=None, max_length=220)

    @field_validator("message")
    @classmethod
    def _clean_message(cls, value: str | None) -> str | None:
        return _normalize_note(value)


class SafetyEventResponse(BaseModel):
    id: str
    event_type: str
    status: str
    lat: float
    lon: float
    note: str | None = None
    message_preview: str
    created_at: str


class SafetyEventListResponse(BaseModel):
    events: list[SafetyEventResponse]


class SafetyStatusResponse(BaseModel):
    departure_port: str
    departure_status: str
    safety_score: int
    gps_status: str
    last_sync_mode: str
    emergency_contacts: list[str]
    emergency_message_preview: str
    blocking_reasons: list[str]
    recommended_checks: list[str]
    recommended_action: str
    last_check_in_at: str | None = None
    open_incidents: int = 0
