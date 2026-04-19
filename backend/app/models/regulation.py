from pydantic import BaseModel, Field


class ProtectedAreaMatch(BaseModel):
    name: str
    status: str
    distance_km: float
    proximity: str


class RegulationAssessmentResponse(BaseModel):
    lat: float
    lon: float
    species: str | None = None
    gear: str | None = None
    license_type: str | None = None
    date: str
    fishing_zone: str
    overall_status: str
    protected_areas: list[ProtectedAreaMatch] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    advisories: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)

