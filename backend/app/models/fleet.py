from pydantic import BaseModel, Field, field_validator, model_validator


class FleetPositionCreate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    speed_kmh: float = Field(default=0.0, ge=0)
    heading_deg: float = Field(default=0.0, ge=0, le=360)
    is_at_sea: bool = True
    note: str | None = None

    @field_validator("note")
    @classmethod
    def _normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None

    @model_validator(mode="after")
    def _validate_operational_area(self) -> "FleetPositionCreate":
        if self.is_at_sea and not (33.0 <= self.lat <= 35.2 and 9.5 <= self.lon <= 11.5):
            raise ValueError(
                "Fleet positions must stay within the wider Gulf of Gabes operational area"
            )
        if not self.is_at_sea and self.speed_kmh > 12:
            raise ValueError("Harbor or on-land positions cannot keep a high navigation speed")
        return self


class FleetPositionSnapshot(BaseModel):
    user_id: str
    full_name: str
    boat_name: str
    lat: float
    lon: float
    speed_kmh: float
    heading_deg: float
    recorded_at: str
    is_at_sea: bool
    assigned_zone_id: str | None = None
    assigned_zone_label: str | None = None


class ZoneLoadSnapshot(BaseModel):
    zone_id: str
    zone_label: str
    active_boats: int
    recommended_boats: int = 0
    capacity: int
    saturation_ratio: float
    predicted_pressure: float = 0.0
    pressure_ratio: float = 0.0


class FleetOverviewResponse(BaseModel):
    active_boats: int
    active_positions: list[FleetPositionSnapshot]
    zone_loads: list[ZoneLoadSnapshot]
