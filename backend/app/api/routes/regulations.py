from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import get_current_user
from app.models.profile import FishermanProfilePublic
from app.models.regulation import RegulationAssessmentResponse
from app.services.regulatory_service import regulatory_service

router = APIRouter()


@router.get("/check", response_model=RegulationAssessmentResponse)
def check_regulations(
    lat: float = Query(...),
    lon: float = Query(...),
    species: str | None = Query(default=None),
    gear: str | None = Query(default=None),
    license_type: str | None = Query(default=None),
    current_date: str | None = Query(default=None, description="YYYY-MM-DD"),
) -> RegulationAssessmentResponse:
    return regulatory_service.assess(
        lat=lat,
        lon=lon,
        species=species,
        gear=gear,
        license_type=license_type,
        current_date=current_date,
    )


@router.get("/check/me", response_model=RegulationAssessmentResponse)
def check_regulations_for_current_user(
    lat: float = Query(...),
    lon: float = Query(...),
    current_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> RegulationAssessmentResponse:
    return regulatory_service.assess_for_profile(
        lat=lat,
        lon=lon,
        profile=current_user,
        current_date=current_date,
    )

