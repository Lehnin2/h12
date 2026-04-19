from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.ports import TARGET_PORTS
from app.domain.regulation_rules import GEAR_BANS, LICENSE_ALLOWED_GEARS, SPECIES_SEASONS
from app.domain.species import SPECIES_PROFILES

VALID_PORT_IDS = {port.id for port in TARGET_PORTS}
VALID_LICENSE_TYPES = set(LICENSE_ALLOWED_GEARS)
VALID_SPECIES = set(SPECIES_PROFILES) | set(SPECIES_SEASONS)


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_tokens(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in values:
        cleaned = _clean_text(item).lower()
        if cleaned and cleaned not in seen:
            normalized.append(cleaned)
            seen.add(cleaned)
    return normalized


class EmergencyContact(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    phone: str = Field(..., min_length=6, max_length=24)
    relation: str = Field(..., min_length=2, max_length=40)

    @field_validator("name", "phone", "relation")
    @classmethod
    def _normalize_text_fields(cls, value: str) -> str:
        return _clean_text(value)


class FishermanProfileBase(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=80)
    license_number: str | None = Field(default=None, max_length=40)
    license_type: str = "artisanal"
    home_port: str = "zarrat"
    boat_name: str = Field(..., min_length=2, max_length=80)
    boat_length_m: float = Field(..., ge=3.0, le=40.0)
    engine_hp: int = Field(..., ge=5, le=1400)
    fuel_capacity_l: float = Field(..., ge=20.0, le=6000.0)
    fuel_consumption_l_per_hour: float = Field(..., ge=1.0, le=500.0)
    fishing_gears: list[str] = Field(default_factory=list)
    target_species: list[str] = Field(default_factory=list)
    emergency_contacts: list[EmergencyContact] = Field(default_factory=list)
    avatar_url: str | None = Field(default=None, max_length=2048)

    @field_validator("full_name", "boat_name")
    @classmethod
    def _normalize_required_text(cls, value: str) -> str:
        return _clean_text(value)

    @field_validator("license_number")
    @classmethod
    def _normalize_license_number(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _clean_text(value)
        return cleaned or None

    @field_validator("license_type")
    @classmethod
    def _validate_license_type(cls, value: str) -> str:
        normalized = _clean_text(value).lower()
        if normalized not in VALID_LICENSE_TYPES:
            raise ValueError(
                f"license_type must be one of: {', '.join(sorted(VALID_LICENSE_TYPES))}"
            )
        return normalized

    @field_validator("home_port")
    @classmethod
    def _validate_home_port(cls, value: str) -> str:
        normalized = _clean_text(value).lower()
        if normalized not in VALID_PORT_IDS:
            raise ValueError(f"home_port must be one of: {', '.join(sorted(VALID_PORT_IDS))}")
        return normalized

    @field_validator("fishing_gears")
    @classmethod
    def _validate_fishing_gears(cls, values: list[str]) -> list[str]:
        normalized = _normalize_tokens(values)
        for gear in normalized:
            if gear in GEAR_BANS:
                raise ValueError(f"{gear} is prohibited and cannot be registered as fishing gear")
        return normalized

    @field_validator("target_species")
    @classmethod
    def _validate_target_species(cls, values: list[str]) -> list[str]:
        normalized = _normalize_tokens(values)
        invalid = [species for species in normalized if species not in VALID_SPECIES]
        if invalid:
            raise ValueError(
                f"Unknown target species: {', '.join(invalid)}. Allowed values include: "
                f"{', '.join(sorted(VALID_SPECIES))}"
            )
        return normalized

    @field_validator("emergency_contacts")
    @classmethod
    def _validate_contacts_count(cls, contacts: list[EmergencyContact]) -> list[EmergencyContact]:
        if len(contacts) > 3:
            raise ValueError("At most 3 emergency contacts are supported")
        return contacts

    @model_validator(mode="after")
    def _validate_profile_coherence(self) -> "FishermanProfileBase":
        allowed_gears = LICENSE_ALLOWED_GEARS[self.license_type]
        invalid_gears = [gear for gear in self.fishing_gears if gear not in allowed_gears]
        if invalid_gears:
            raise ValueError(
                f"License type '{self.license_type}' does not allow: {', '.join(invalid_gears)}"
            )

        if self.fuel_capacity_l < self.fuel_consumption_l_per_hour * 2:
            raise ValueError(
                "Fuel capacity is too low for the declared hourly consumption; "
                "the profile would not support even a short mission window."
            )

        if self.boat_length_m <= 6 and self.engine_hp > 250:
            raise ValueError("Engine power is too high for the declared small boat length")

        if self.boat_length_m >= 18 and self.engine_hp < 60:
            raise ValueError("Engine power is too low for the declared boat length")

        return self


class FishermanProfileCreate(FishermanProfileBase):
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        normalized = _clean_text(value).lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("email must be a valid address")
        return normalized


class FishermanProfileUpdate(FishermanProfileBase):
    pass


class FishermanProfilePublic(FishermanProfileBase):
    id: str
    email: str
    is_admin: bool = False
