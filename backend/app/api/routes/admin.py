from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_admin
from app.models.admin import AdminOverviewResponse
from app.models.profile import FishermanProfilePublic
from app.services.admin_service import admin_service

router = APIRouter()


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(
    admin_user: FishermanProfilePublic = Depends(get_current_admin),
) -> AdminOverviewResponse:
    return admin_service.overview(admin_user)
