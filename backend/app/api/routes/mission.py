from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import get_current_user
from app.models.mission import MissionBriefingResponse, MissionHistoryResponse
from app.models.profile import FishermanProfilePublic
from app.services.mission_service import mission_service

router = APIRouter()


@router.get("/briefing", response_model=MissionBriefingResponse)
def get_mission_briefing(
    departure_port: str = Query(default="zarrat"),
    species: str = Query(default="poulpe"),
) -> MissionBriefingResponse:
    return mission_service.build_briefing(departure_port, species)


@router.get("/briefing/me", response_model=MissionBriefingResponse)
def get_personalized_mission_briefing(
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> MissionBriefingResponse:
    return mission_service.build_briefing_for_user(current_user)


@router.get("/history", response_model=MissionHistoryResponse)
def get_mission_history(limit: int = Query(default=20, ge=1, le=100)) -> MissionHistoryResponse:
    return mission_service.history(limit)


@router.get("/history/me", response_model=MissionHistoryResponse)
def get_my_mission_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> MissionHistoryResponse:
    return mission_service.history_for_user(current_user.id, limit)
