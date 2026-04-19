from fastapi import APIRouter, HTTPException

from app.models.sonar import SonarPredictRequest, SonarPredictionResponse, SonarStatusResponse
from app.services.sonar_service import sonar_service

router = APIRouter()


@router.get("/status", response_model=SonarStatusResponse)
def sonar_status() -> SonarStatusResponse:
    return sonar_service.status()


@router.post("/predict", response_model=SonarPredictionResponse)
def sonar_predict(payload: SonarPredictRequest) -> SonarPredictionResponse:
    try:
        return sonar_service.predict(payload.readings)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

