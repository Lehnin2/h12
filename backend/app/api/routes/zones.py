from fastapi import APIRouter, Query

from app.models.zone import HeatmapResponse, RecommendationResponse
from app.services.catalog_service import catalog_service
from app.services.zone_engine import zone_engine

router = APIRouter()


@router.get("/ports")
def list_ports() -> dict[str, object]:
    return {"ports": catalog_service.list_ports()}


@router.get("/heatmap", response_model=HeatmapResponse)
def get_heatmap(
    departure_port: str = Query(default="zarrat"),
    species: str = Query(default="poulpe"),
) -> HeatmapResponse:
    return zone_engine.build_heatmap(departure_port, species)


@router.get("/recommend", response_model=RecommendationResponse)
def get_recommendation(
    departure_port: str = Query(default="zarrat"),
    species: str = Query(default="poulpe"),
) -> RecommendationResponse:
    return zone_engine.recommend(departure_port, species)

