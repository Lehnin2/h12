from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps.auth import get_current_user
from app.models.profile import FishermanProfilePublic
from app.models.report import (
    CommunityReportCreate,
    CommunityReportFeedResponse,
    CommunityReportSnapshot,
    ZoneReportSummary,
)
from app.services.report_service import report_service

router = APIRouter()


@router.post("/submit")
def submit_report(
    payload: CommunityReportCreate,
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> dict[str, str]:
    report_service.submit_report(current_user.id, payload)
    return {"status": "report_recorded"}


@router.get("/recent", response_model=CommunityReportFeedResponse)
def get_recent_reports(
    within_hours: int = Query(default=72, ge=1, le=336),
) -> CommunityReportFeedResponse:
    return report_service.feed(within_hours)


@router.get("/nearby", response_model=list[CommunityReportSnapshot])
def get_nearby_reports(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=20.0, ge=1.0, le=80.0),
    within_hours: int = Query(default=72, ge=1, le=336),
) -> list[CommunityReportSnapshot]:
    return report_service.list_nearby_reports(lat, lon, radius_km, within_hours)


@router.get("/zone/{zone_id}", response_model=ZoneReportSummary)
def get_zone_report_summary(
    zone_id: str,
    within_hours: int = Query(default=72, ge=1, le=336),
) -> ZoneReportSummary:
    try:
        return report_service.zone_summary(zone_id, within_hours)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown zone: {zone_id}") from error

