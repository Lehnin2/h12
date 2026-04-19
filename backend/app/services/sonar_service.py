from __future__ import annotations

from math import exp, floor
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import settings
from app.models.sonar import (
    SonarEngineeredFeatures,
    SonarPredictionResponse,
    SonarStatusResponse,
)

try:
    import joblib  # type: ignore
except ImportError:  # pragma: no cover - optional dependency in local environment
    joblib = None


class SonarService:
    def __init__(self) -> None:
        self._load_attempted = False
        self._model: Any | None = None
        self._scaler: Any | None = None
        self._load_error: str | None = None

    def _ensure_loaded(self) -> None:
        if self._load_attempted:
            return

        self._load_attempted = True
        model_path = Path(settings.sonar_model_path)
        scaler_path = Path(settings.sonar_scaler_path)

        if joblib is None:
            self._load_error = "joblib/scikit-learn dependencies are not installed."
            return

        if not model_path.exists():
            self._load_error = f"Model file not found at {model_path}"
            return

        try:
            self._model = joblib.load(model_path)
        except Exception as error:  # pragma: no cover - depends on local sklearn env
            self._load_error = f"Unable to load sonar model: {error}"
            return

        if scaler_path.exists():
            try:
                self._scaler = joblib.load(scaler_path)
            except Exception as error:  # pragma: no cover - depends on local sklearn env
                self._load_error = f"Model loaded but scaler failed to load: {error}"
        else:
            self._scaler = None

    def status(self) -> SonarStatusResponse:
        self._ensure_loaded()
        warnings: list[str] = []

        if self._model is None:
            detail = self._load_error or "Sonar model unavailable."
            return SonarStatusResponse(
                available=False,
                model_loaded=False,
                scaler_loaded=False,
                mode="unavailable",
                warnings=[detail],
                detail=detail,
            )

        mode = "model+scaler" if self._scaler is not None else "model_without_scaler"
        if self._scaler is None:
            warnings.append(
                "Scaler file not found. The service assumes the incoming sonar distribution already matches training expectations."
            )
        if self._load_error and self._scaler is None:
            warnings.append(self._load_error)

        return SonarStatusResponse(
            available=True,
            model_loaded=True,
            scaler_loaded=self._scaler is not None,
            mode=mode,
            warnings=warnings,
            detail="Sonar prediction service is available.",
        )

    def _engineer_features(self, readings: list[float]) -> SonarEngineeredFeatures:
        values = np.asarray(readings, dtype=float)
        bands = np.arange(1, 61, dtype=float)
        epsilon = 1e-9

        total_energy = float(values.sum())
        peak_band = int(np.argmax(values) + 1)
        spectral_centroid = float((values * bands).sum() / (total_energy + epsilon))
        bandwidth = float(
            np.sqrt((values * (bands - spectral_centroid) ** 2).sum() / (total_energy + epsilon))
        )
        low_high_ratio = float(values[:20].sum() / (values[40:].sum() + epsilon))
        mid_energy = float(values[20:40].sum())
        energy_gradient = float(np.polyfit(bands, values, 1)[0])
        probabilities = values / (total_energy + epsilon)
        spectral_entropy = float(-(probabilities * np.log(probabilities + epsilon)).sum())
        rms = float(np.sqrt((values**2).mean()))
        bearing_deg = float(((spectral_centroid - 1.0) / 59.0) * 360.0)
        rel_distance = float(1.0 - min(total_energy / settings.sonar_empirical_max_energy, 1.0))

        return SonarEngineeredFeatures(
            total_energy=round(total_energy, 6),
            peak_band=peak_band,
            spectral_centroid=round(spectral_centroid, 6),
            bandwidth=round(bandwidth, 6),
            low_high_ratio=round(low_high_ratio, 6),
            mid_energy=round(mid_energy, 6),
            energy_gradient=round(energy_gradient, 6),
            spectral_entropy=round(spectral_entropy, 6),
            rms=round(rms, 6),
            bearing_deg=round(bearing_deg, 3),
            rel_distance=round(rel_distance, 6),
        )

    def _feature_vector(
        self,
        readings: list[float],
        engineered: SonarEngineeredFeatures,
    ) -> np.ndarray:
        return np.asarray(
            [
                *readings,
                engineered.total_energy,
                engineered.peak_band,
                engineered.spectral_centroid,
                engineered.bandwidth,
                engineered.low_high_ratio,
                engineered.mid_energy,
                engineered.energy_gradient,
                engineered.spectral_entropy,
                engineered.rms,
                engineered.bearing_deg,
                engineered.rel_distance,
            ],
            dtype=float,
        )

    def _cardinal_direction(self, bearing_deg: float) -> str:
        cardinals = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]
        card_index = int(floor((bearing_deg + 11.25) / 22.5)) % 16
        return cardinals[card_index]

    def _distance_label(self, rel_distance: float) -> str:
        if rel_distance < 0.33:
            return "CLOSE (<200m est.)"
        if rel_distance < 0.66:
            return "MEDIUM (200-500m est.)"
        return "FAR (>500m est.)"

    def _confidence(self, model: Any, vector: np.ndarray, predicted_class: int) -> float:
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(vector.reshape(1, -1))[0]
            return float(probabilities[predicted_class])

        if hasattr(model, "decision_function"):
            score = float(model.decision_function(vector.reshape(1, -1))[0])
            probability = 1.0 / (1.0 + exp(-score))
            return probability if predicted_class == 1 else 1.0 - probability

        return 0.5

    def predict(self, readings: list[float]) -> SonarPredictionResponse:
        self._ensure_loaded()
        if self._model is None:
            raise RuntimeError(self._load_error or "Sonar model is not available.")

        engineered = self._engineer_features(readings)
        vector = self._feature_vector(readings, engineered)
        warnings: list[str] = []
        scaler_applied = False

        if self._scaler is not None:
            vector = self._scaler.transform(vector.reshape(1, -1))[0]
            scaler_applied = True
            mode = "model+scaler"
        else:
            mode = "model_without_scaler"
            warnings.append(
                "Scaler file not found. Prediction assumes the provided 60 sonar readings are already normalized and comparable to training inputs."
            )

        predicted_class = int(self._model.predict(vector.reshape(1, -1))[0])
        confidence = self._confidence(self._model, vector, predicted_class)
        bearing_deg = engineered.bearing_deg
        cardinal = self._cardinal_direction(bearing_deg)
        dist_label = self._distance_label(engineered.rel_distance)
        detection = "Mine/Fish Target" if predicted_class == 1 else "Rock"

        description = (
            f"SONAR DETECTION: {detection} | "
            f"Confidence: {confidence:.1%} | "
            f"Bearing: {bearing_deg:.1f}° ({cardinal}) | "
            f"Distance: {dist_label} (rel={engineered.rel_distance:.2f})"
        )

        return SonarPredictionResponse(
            available=True,
            mode=mode,
            scaler_applied=scaler_applied,
            detection=detection,
            predicted_class=predicted_class,
            confidence=round(confidence, 6),
            bearing_deg=bearing_deg,
            cardinal=cardinal,
            rel_distance=engineered.rel_distance,
            dist_label=dist_label,
            description=description,
            engineered_features=engineered,
            warnings=warnings,
        )


sonar_service = SonarService()

