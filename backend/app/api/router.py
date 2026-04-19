from fastapi import APIRouter

from app.api.routes import (
    admin,
    auth,
    bathymetry,
    chat,
    fleet,
    lunar,
    mission,
    pollution,
    regulations,
    reports,
    routing,
    safety,
    satellite,
    sonar,
    weather,
    zones,
)

api_router = APIRouter()
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(zones.router, prefix="/zones", tags=["zones"])
api_router.include_router(fleet.router, prefix="/fleet", tags=["fleet"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(pollution.router, prefix="/pollution", tags=["pollution"])
api_router.include_router(regulations.router, prefix="/regulations", tags=["regulations"])
api_router.include_router(routing.router, prefix="/route", tags=["routing"])
api_router.include_router(lunar.router, prefix="/lunar", tags=["lunar"])
api_router.include_router(safety.router, prefix="/safety", tags=["safety"])
api_router.include_router(satellite.router, prefix="/satellite", tags=["satellite"])
api_router.include_router(sonar.router, prefix="/sonar", tags=["sonar"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(bathymetry.router, prefix="/bathymetry", tags=["bathymetry"])
api_router.include_router(mission.router, prefix="/mission", tags=["mission"])
