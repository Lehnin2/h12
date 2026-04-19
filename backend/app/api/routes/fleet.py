from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps.auth import get_current_user
from app.models.fleet import FleetOverviewResponse, FleetPositionCreate, ZoneLoadSnapshot
from app.models.profile import FishermanProfilePublic
from app.services.fleet_service import fleet_service

router = APIRouter()


@router.post("/position")
def update_fleet_position(
    payload: FleetPositionCreate,
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> dict[str, str]:
    fleet_service.register_position(current_user.id, payload)
    return {"status": "position_recorded"}


@router.get("/active", response_model=FleetOverviewResponse)
def get_active_fleet(
    within_minutes: int = Query(default=240, ge=5, le=1440),
) -> FleetOverviewResponse:
    return fleet_service.overview(within_minutes)


@router.get("/load/{zone_id}", response_model=ZoneLoadSnapshot)
def get_zone_load(zone_id: str) -> ZoneLoadSnapshot:
    loads = fleet_service.compute_zone_loads()
    try:
        return loads[zone_id]
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown zone: {zone_id}") from error
