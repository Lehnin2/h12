from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps.auth import get_current_user
from app.models.auth import AuthResponse, LoginRequest
from app.models.profile import (
    FishermanProfileCreate,
    FishermanProfilePublic,
    FishermanProfileUpdate,
)
from app.services.auth_service import auth_service

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/register", response_model=AuthResponse)
def register(payload: FishermanProfileCreate) -> AuthResponse:
    return auth_service.register(payload)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    return auth_service.login(payload)


@router.get("/me", response_model=FishermanProfilePublic)
def me(current_user: FishermanProfilePublic = Depends(get_current_user)) -> FishermanProfilePublic:
    return current_user


@router.put("/profile", response_model=FishermanProfilePublic)
def update_profile(
    payload: FishermanProfileUpdate,
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> FishermanProfilePublic:
    return auth_service.update_profile(current_user.id, payload)


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, str]:
    if credentials is not None and credentials.credentials:
        auth_service.logout(credentials.credentials)
    return {"status": "logged_out"}
