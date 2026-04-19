from fastapi import APIRouter, Query

from app.models.routing import RouteResponse
from app.services.routing_service import routing_service

router = APIRouter()


@router.get("/optimize", response_model=RouteResponse)
def optimize_route(
    departure_port: str = Query(default="zarrat"),
    target_zone_id: str = Query(default="zarrat_c3"),
) -> RouteResponse:
    return routing_service.optimize(departure_port, target_zone_id)

