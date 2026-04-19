from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from math import atan2, cos, degrees, radians, sin

from app.domain.zone_seed import SEEDED_ZONES
from app.models.pollution import (
    PollutionObservationResponse,
    PollutionOverviewResponse,
    PollutionPlumeSnapshot,
    PollutionSourceSnapshot,
    PollutionZoneResponse,
)
from app.repositories.pollution_repository import pollution_repository
from app.services.report_service import report_service
from app.services.satellite_service import satellite_service
from app.services.utils import haversine_km
from app.services.weather_service import weather_service


class PollutionService:
    cache_ttl = timedelta(minutes=75)

    def __init__(self) -> None:
        self._response_cache: dict[tuple[float, float], tuple[datetime, PollutionObservationResponse]] = {}

    def _cached(self, lat: float, lon: float) -> PollutionObservationResponse | None:
        key = (round(lat, 3), round(lon, 3))
        cached = self._response_cache.get(key)
        if cached is not None:
            cached_at, payload = cached
            if datetime.now(UTC) - cached_at <= self.cache_ttl:
                return payload
        persisted = pollution_repository.get_recent_observation(lat, lon, self.cache_ttl)
        if persisted is not None:
            self._response_cache[key] = (datetime.now(UTC), persisted)
        return persisted

    def _store_cache(self, payload: PollutionObservationResponse) -> PollutionObservationResponse:
        key = (round(payload.lat, 3), round(payload.lon, 3))
        self._response_cache[key] = (datetime.now(UTC), payload)
        pollution_repository.store_observation(payload)
        return payload

    def _bearing_deg(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> float:
        lat1 = radians(start_lat)
        lat2 = radians(end_lat)
        diff_lon = radians(end_lon - start_lon)
        x = sin(diff_lon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(diff_lon)
        return (degrees(atan2(x, y)) + 360.0) % 360.0

    def _direction_alignment(self, plume_direction_deg: float | None, point_bearing_deg: float) -> float:
        if plume_direction_deg is None:
            return 0.55
        diff = abs((plume_direction_deg - point_bearing_deg + 180) % 360 - 180)
        return max(0.18, 1.0 - diff / 180)

    def list_sources(self) -> list[PollutionSourceSnapshot]:
        return pollution_repository.list_sources()

    def _advisory(self, risk_score: float, source_name: str | None, contamination_index: int) -> str:
        origin = source_name or "regional plume source"
        if risk_score >= 0.78:
            return f"High contamination risk from {origin}. Avoid catch extraction and reroute to cleaner sectors."
        if risk_score >= 0.52:
            return f"Moderate plume influence linked to {origin}. Verify fish quality and limit exposure time."
        if contamination_index >= 28:
            return f"Low to moderate contamination signal influenced by {origin}. Keep monitoring during departure."
        return "Pollution pressure is currently limited for this point compared with the inner Gulf plume corridor."

    def get_point_assessment(self, lat: float, lon: float) -> PollutionObservationResponse:
        cached = self._cached(lat, lon)
        if cached is not None:
            return cached

        sources = [source for source in self.list_sources() if source.status in {"active", "seasonal"}]
        weather = weather_service.get_point_forecast(lat, lon, hours=3)
        satellite = satellite_service.get_point_observation(lat, lon)
        nearby_reports = report_service.list_nearby_reports(lat, lon, radius_km=18, within_hours=72)
        pollution_reports = [report for report in nearby_reports if report.report_type == "pollution"]

        wind_direction = weather.current.wind_direction_deg or 145.0
        wind_speed = weather.current.wind_speed_kmh or 14.0
        current_speed = satellite.current_speed_kmh or weather.current.current_speed_kmh or 2.0
        spread_speed_kmh = round(wind_speed * 0.42 + current_speed * 0.38, 1)

        best_source: PollutionSourceSnapshot | None = None
        best_risk = 0.0
        best_radius = 6.0
        best_direction = wind_direction
        for source in sources:
            distance = haversine_km(source.lat, source.lon, lat, lon)
            point_bearing = self._bearing_deg(source.lat, source.lon, lat, lon)
            plume_direction = (wind_direction * 0.7 + point_bearing * 0.1 + 0.2 * 165.0) % 360
            plume_radius = round(7.0 + wind_speed * 0.18 + current_speed * 0.35 + source.base_severity * 9.0, 1)
            decay = max(0.0, 1.0 - distance / max(plume_radius, 0.1))
            alignment = self._direction_alignment(plume_direction, point_bearing)
            seasonal_bonus = 1.08 if source.status == "seasonal" and weather.current.precipitation_mm_per_hour else 1.0
            report_boost = 1 + min(len(pollution_reports) * 0.08, 0.24)
            risk = min(source.base_severity * decay * alignment * seasonal_bonus * report_boost, 1.0)
            if risk > best_risk:
                best_risk = risk
                best_source = source
                best_radius = plume_radius
                best_direction = plume_direction

        contamination_index = max(
            3,
            min(
                100,
                round(
                    best_risk * 100
                    + min((satellite.chlorophyll_mg_m3 or 0.0) * 6, 10)
                    + min(len(pollution_reports) * 6, 16)
                ),
            ),
        )
        advisory = self._advisory(best_risk, best_source.name if best_source else None, contamination_index)
        is_live = weather.is_live or satellite.is_live
        payload = PollutionObservationResponse(
            lat=lat,
            lon=lon,
            source="hybrid_plume_model",
            status="success",
            is_live=is_live,
            observed_at=datetime.now(UTC).isoformat(),
            nearest_source_id=best_source.id if best_source else None,
            nearest_source_name=best_source.name if best_source else None,
            risk_score=round(best_risk, 2),
            contamination_index=contamination_index,
            plume_direction_deg=round(best_direction, 1) if best_source else None,
            plume_radius_km=best_radius if best_source else None,
            spread_speed_kmh=spread_speed_kmh,
            advisory=advisory,
        )
        if best_source is not None:
            plume = PollutionPlumeSnapshot(
                source_id=best_source.id,
                source_name=best_source.name,
                center_lat=best_source.lat,
                center_lon=best_source.lon,
                observed_at=payload.observed_at,
                plume_direction_deg=round(best_direction, 1),
                plume_radius_km=best_radius,
                spread_speed_kmh=spread_speed_kmh,
                core_risk=round(best_source.base_severity, 2),
                geometry_hint_json=json.dumps(
                    {
                        "shape": "sector",
                        "radius_km": best_radius,
                        "direction_deg": round(best_direction, 1),
                        "spread_speed_kmh": spread_speed_kmh,
                    }
                ),
            )
            pollution_repository.store_plume_snapshot(plume)
        return self._store_cache(payload)

    def get_zone_assessment(self, zone_id: str) -> PollutionZoneResponse:
        zone = next((item for item in SEEDED_ZONES if item.id == zone_id), SEEDED_ZONES[0])
        return PollutionZoneResponse(
            zone_id=zone.id,
            zone_label=zone.label,
            observation=self.get_point_assessment(zone.center_lat, zone.center_lon),
        )

    def overview(self, within_hours: int = 48) -> PollutionOverviewResponse:
        return PollutionOverviewResponse(
            sources=self.list_sources(),
            recent_plumes=pollution_repository.list_recent_plumes(within_hours=within_hours),
        )


pollution_service = PollutionService()

