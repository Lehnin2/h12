from pydantic import BaseModel, Field, field_validator

from app.models.profile import FishermanProfilePublic


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        normalized = " ".join(value.strip().split()).lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("email must be a valid address")
        return normalized


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    profile: FishermanProfilePublic
