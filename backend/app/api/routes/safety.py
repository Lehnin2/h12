from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import get_current_user
from app.models.profile import FishermanProfilePublic
from app.models.safety import (
    SafetyCheckInCreate,
    SafetyEventListResponse,
    SafetyEventResponse,
    SafetySosCreate,
    SafetyStatusResponse,
)
from app.services.safety_service import safety_service

router = APIRouter()


@router.get("/status", response_model=SafetyStatusResponse)
def safety_status(departure_port: str = Query(default="zarrat")) -> SafetyStatusResponse:
    return safety_service.get_status(departure_port)


@router.get("/status/me", response_model=SafetyStatusResponse)
def safety_status_me(
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> SafetyStatusResponse:
    return safety_service.get_status(current_user.home_port, profile=current_user)


@router.post("/check-in", response_model=SafetyEventResponse)
def create_safety_check_in(
    payload: SafetyCheckInCreate,
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> SafetyEventResponse:
    return safety_service.create_check_in(current_user, payload)


@router.post("/sos", response_model=SafetyEventResponse)
def trigger_safety_sos(
    payload: SafetySosCreate,
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> SafetyEventResponse:
    return safety_service.trigger_sos(current_user, payload)


@router.get("/events/me", response_model=SafetyEventListResponse)
def list_my_safety_events(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> SafetyEventListResponse:
    return safety_service.list_events(current_user.id, limit)
