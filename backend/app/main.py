from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.database import init_database
from app.services.auth_service import auth_service


def create_app() -> FastAPI:
    init_database()
    auth_service.ensure_seed_admin()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "Guardian of the Gulf API for intelligent fishing zone guidance, "
            "eco-routing, lunar recommendations, and safety flows."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
