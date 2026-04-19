from pydantic import BaseModel, Field, field_validator


class SonarPredictRequest(BaseModel):
    readings: list[float] = Field(..., min_length=60, max_length=60)

    @field_validator("readings")
    @classmethod
    def _validate_finite_values(cls, value: list[float]) -> list[float]:
        for item in value:
            if item != item or item in {float("inf"), float("-inf")}:
                raise ValueError("readings must contain only finite float values")
        return value


class SonarEngineeredFeatures(BaseModel):
    total_energy: float
    peak_band: int
    spectral_centroid: float
    bandwidth: float
    low_high_ratio: float
    mid_energy: float
    energy_gradient: float
    spectral_entropy: float
    rms: float
    bearing_deg: float
    rel_distance: float


class SonarStatusResponse(BaseModel):
    available: bool
    model_loaded: bool
    scaler_loaded: bool
    mode: str
    expected_raw_bands: int = 60
    expected_feature_count: int = 71
    warnings: list[str] = Field(default_factory=list)
    detail: str


class SonarPredictionResponse(BaseModel):
    available: bool
    mode: str
    scaler_applied: bool
    raw_band_count: int = 60
    feature_count: int = 71
    detection: str
    predicted_class: int
    confidence: float
    bearing_deg: float
    cardinal: str
    rel_distance: float
    dist_label: str
    description: str
    engineered_features: SonarEngineeredFeatures
    warnings: list[str] = Field(default_factory=list)

