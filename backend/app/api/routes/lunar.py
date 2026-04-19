from fastapi import APIRouter, Query

from app.models.lunar import LunarResponse
from app.services.lunar_service import lunar_service

router = APIRouter()


@router.get("/today", response_model=LunarResponse)
def lunar_today(species: str = Query(default="poulpe")) -> LunarResponse:
    return lunar_service.get_today(species)

