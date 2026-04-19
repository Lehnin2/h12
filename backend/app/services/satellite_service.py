from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import atan2, cos, degrees, sin
from typing import Any

from app.core.config import settings
from app.domain.zone_seed import SEEDED_ZONES
from app.models.satellite import SatelliteObservationResponse, SatelliteZoneResponse
from app.repositories.satellite_repository import satellite_repository
from app.services.utils import haversine_km

try:
    import copernicusmarine  # type: ignore
except ImportError:  # pragma: no cover - optional dependency in local environment
    copernicusmarine = None


class SatelliteService:
    cache_ttl = timedelta(minutes=90)
    sst_variable_candidates = [
        "analysed_sst",
        "sea_surface_temperature",
        "sst",
    ]
    chlorophyll_variable_candidates = [
        "CHL",
        "chl",
        "chlorophyll",
        "mass_concentration_of_chlorophyll_a_in_sea_water",
    ]
    salinity_variable_candidates = [
        "so",
        "sos",
        "salinity",
        "sea_water_salinity",
        "sea_surface_salinity",
    ]
    turbidity_variable_candidates = [
        "TUR",
        "tur",
        "turbidity",
        "sea_water_turbidity",
    ]
    suspended_matter_variable_candidates = [
        "SPM",
        "spm",
        "suspended_matter",
        "mass_concentration_of_suspended_matter_in_sea_water",
    ]
    current_u_candidates = ["uo", "eastward_sea_water_velocity"]
    current_v_candidates = ["vo", "northward_sea_water_velocity"]

    def __init__(self) -> None:
        self._response_cache: dict[tuple[float, float], tuple[datetime, SatelliteObservationResponse]] = {}

    def _toolbox_ready(self) -> bool:
        return (
            copernicusmarine is not None
            and settings.copernicusmarine_username is not None
            and settings.copernicusmarine_password is not None
        )

    def _cached(self, lat: float, lon: float) -> SatelliteObservationResponse | None:
        key = (round(lat, 3), round(lon, 3))
        cached = self._response_cache.get(key)
        if cached is None:
            return satellite_repository.get_recent_observation(lat, lon, self.cache_ttl)
        cached_at, payload = cached
        if datetime.now(UTC) - cached_at <= self.cache_ttl:
            return payload
        persisted = satellite_repository.get_recent_observation(lat, lon, self.cache_ttl)
        if persisted is None:
            return None
        self._response_cache[key] = (datetime.now(UTC), persisted)
        return persisted

    def _store_cache(self, payload: SatelliteObservationResponse) -> SatelliteObservationResponse:
        key = (round(payload.lat, 3), round(payload.lon, 3))
        self._response_cache[key] = (datetime.now(UTC), payload)
        satellite_repository.upsert_observation(payload)
        return payload

    def _extract_scalar(self, dataset: Any, candidates: list[str]) -> float | None:
        for variable in candidates:
            if variable not in dataset.data_vars:
                continue
            data_array = dataset[variable]
            try:
                for dimension in ("time", "depth", "latitude", "longitude"):
                    if dimension in data_array.dims and data_array.sizes.get(dimension, 0) > 0:
                        data_array = data_array.isel({dimension: -1 if dimension == "time" else 0})
                value = data_array.values
                if hasattr(value, "item"):
                    value = value.item()
                return float(value)
            except Exception:
                continue
        return None

    def _open_dataset(
        self,
        dataset_id: str,
        variables: list[str],
        lat: float,
        lon: float,
        start_datetime: datetime,
        end_datetime: datetime,
        minimum_depth: float | None = None,
        maximum_depth: float | None = None,
    ) -> Any | None:
        if not self._toolbox_ready():
            return None
        try:
            return copernicusmarine.open_dataset(
                dataset_id=dataset_id,
                username=settings.copernicusmarine_username,
                password=settings.copernicusmarine_password,
                variables=variables,
                minimum_longitude=lon,
                maximum_longitude=lon,
                minimum_latitude=lat,
                maximum_latitude=lat,
                start_datetime=start_datetime.isoformat(),
                end_datetime=end_datetime.isoformat(),
                minimum_depth=minimum_depth,
                maximum_depth=maximum_depth,
                coordinates_selection_method="nearest",
            )
        except Exception:
            return None

    def _direction_from_uv(self, u_value: float | None, v_value: float | None) -> float | None:
        if u_value is None or v_value is None:
            return None
        angle = (degrees(atan2(u_value, v_value)) + 360.0) % 360.0
        return round(angle, 1)

    def _advisory(
        self,
        productivity_index: int,
        chlorophyll_mg_m3: float | None,
        turbidity_fnu: float | None,
        current_speed_kmh: float | None,
    ) -> tuple[str, str]:
        chlorophyll = chlorophyll_mg_m3 or 0.0
        turbidity = turbidity_fnu or 0.0
        current = current_speed_kmh or 0.0
        turbidity_risk = "LOW"
        if turbidity >= 12 or chlorophyll >= 1.8:
            turbidity_risk = "HIGH"
        elif turbidity >= 5 or chlorophyll >= 1.1:
            turbidity_risk = "MEDIUM"

        if turbidity_risk == "HIGH":
            return (
                turbidity_risk,
                "Satellite turbidity is high near the target waters. Verify plume exposure and fish quality before departure.",
            )
        if productivity_index >= 76 and current <= 5.0:
            return (
                turbidity_risk,
                "Satellite productivity is favorable with manageable surface currents around the target zone.",
            )
        if current >= 7.5:
            return (
                turbidity_risk,
                "Surface currents are strengthening. Prefer shorter loops and conserve fuel margin.",
            )
        return (
            turbidity_risk,
            "Satellite conditions are usable but should be combined with weather, law, and safety filters.",
        )

    def _fallback_observation(self, lat: float, lon: float) -> SatelliteObservationResponse:
        nearest_zone = min(
            SEEDED_ZONES,
            key=lambda zone: haversine_km(lat, lon, zone.center_lat, zone.center_lon),
        )
        sea_bias = abs(sin(lat * 0.4) + cos(lon * 0.35))
        sst_c = round(18.8 + sea_bias * 4.6, 1)
        chlorophyll_mg_m3 = round(max(0.08, nearest_zone.chlorophyll * 1.6 + sea_bias * 0.18), 2)
        salinity_psu = round(37.2 + (sea_bias * 0.65) - nearest_zone.pollution_risk * 0.25, 2)
        turbidity_fnu = round(max(0.7, nearest_zone.pollution_risk * 11 + sea_bias * 1.8), 2)
        suspended_matter_mg_l = round(max(0.6, nearest_zone.pollution_risk * 8.5 + sea_bias * 1.2), 2)
        current_speed_kmh = round(max(0.8, nearest_zone.current_speed * 3.6 + sea_bias * 0.9), 1)
        productivity_index = max(
            15,
            min(
                95,
                round(
                    45
                    + nearest_zone.chlorophyll * 32
                    + max(0.0, 22 - abs(sst_c - 21.5) * 4)
                    - min(turbidity_fnu * 1.8, 18)
                ),
            ),
        )
        turbidity_risk, advisory = self._advisory(
            productivity_index,
            chlorophyll_mg_m3,
            turbidity_fnu,
            current_speed_kmh,
        )
        return SatelliteObservationResponse(
            lat=lat,
            lon=lon,
            source="copernicus_fallback_seeded",
            status="success",
            is_live=False,
            timestamp=datetime.now(UTC).isoformat(),
            sst_c=sst_c,
            chlorophyll_mg_m3=chlorophyll_mg_m3,
            salinity_psu=salinity_psu,
            turbidity_fnu=turbidity_fnu,
            suspended_matter_mg_l=suspended_matter_mg_l,
            current_speed_kmh=current_speed_kmh,
            current_direction_deg=round((145 + sea_bias * 60) % 360, 1),
            productivity_index=productivity_index,
            turbidity_risk=turbidity_risk,
            advisory=advisory,
        )

    def get_point_observation(self, lat: float, lon: float) -> SatelliteObservationResponse:
        cached = self._cached(lat, lon)
        if cached is not None:
            return cached

        if not self._toolbox_ready():
            return self._store_cache(self._fallback_observation(lat, lon))

        now = datetime.now(UTC)
        sst_dataset = self._open_dataset(
            settings.copernicus_sst_dataset_id,
            self.sst_variable_candidates,
            lat,
            lon,
            now - timedelta(days=5),
            now,
        )
        chlorophyll_dataset = self._open_dataset(
            settings.copernicus_chl_dataset_id,
            self.chlorophyll_variable_candidates,
            lat,
            lon,
            now - timedelta(days=5),
            now,
        )
        salinity_dataset = self._open_dataset(
            settings.copernicus_salinity_dataset_id,
            self.salinity_variable_candidates,
            lat,
            lon,
            now - timedelta(days=2),
            now + timedelta(hours=6),
            minimum_depth=0.0,
            maximum_depth=2.0,
        )
        turbidity_dataset = self._open_dataset(
            settings.copernicus_turbidity_dataset_id,
            self.turbidity_variable_candidates + self.suspended_matter_variable_candidates,
            lat,
            lon,
            now - timedelta(days=7),
            now,
        )
        current_dataset = self._open_dataset(
            settings.copernicus_currents_dataset_id,
            self.current_u_candidates + self.current_v_candidates,
            lat,
            lon,
            now - timedelta(hours=24),
            now + timedelta(hours=6),
            minimum_depth=0.0,
            maximum_depth=2.0,
        )

        sst_c = self._extract_scalar(sst_dataset, self.sst_variable_candidates) if sst_dataset is not None else None
        chlorophyll_mg_m3 = (
            self._extract_scalar(chlorophyll_dataset, self.chlorophyll_variable_candidates)
            if chlorophyll_dataset is not None
            else None
        )
        salinity_psu = (
            self._extract_scalar(salinity_dataset, self.salinity_variable_candidates)
            if salinity_dataset is not None
            else None
        )
        turbidity_fnu = (
            self._extract_scalar(turbidity_dataset, self.turbidity_variable_candidates)
            if turbidity_dataset is not None
            else None
        )
        suspended_matter_mg_l = (
            self._extract_scalar(turbidity_dataset, self.suspended_matter_variable_candidates)
            if turbidity_dataset is not None
            else None
        )
        u_current = self._extract_scalar(current_dataset, self.current_u_candidates) if current_dataset is not None else None
        v_current = self._extract_scalar(current_dataset, self.current_v_candidates) if current_dataset is not None else None

        if (
            sst_c is None
            and chlorophyll_mg_m3 is None
            and salinity_psu is None
            and turbidity_fnu is None
            and suspended_matter_mg_l is None
            and u_current is None
            and v_current is None
        ):
            return self._store_cache(self._fallback_observation(lat, lon))

        current_speed_kmh = None
        if u_current is not None and v_current is not None:
            current_speed_kmh = round((((u_current ** 2) + (v_current ** 2)) ** 0.5) * 3.6, 1)
        current_direction_deg = self._direction_from_uv(u_current, v_current)

        productivity_index = 52
        if chlorophyll_mg_m3 is not None:
            productivity_index += round(min(chlorophyll_mg_m3 * 18, 26))
        if sst_c is not None:
            productivity_index += round(max(-10, 18 - abs(sst_c - 21.0) * 3))
        if salinity_psu is not None:
            productivity_index += round(max(-7, 8 - abs(salinity_psu - 37.8) * 8))
        if turbidity_fnu is not None:
            productivity_index -= round(min(max(turbidity_fnu - 3.0, 0.0) * 2.1, 20))
        if current_speed_kmh is not None:
            productivity_index -= round(min(max(current_speed_kmh - 4.5, 0.0) * 2.4, 18))
        productivity_index = max(10, min(95, productivity_index))

        turbidity_risk, advisory = self._advisory(
            productivity_index,
            chlorophyll_mg_m3,
            turbidity_fnu,
            current_speed_kmh,
        )
        payload = SatelliteObservationResponse(
            lat=lat,
            lon=lon,
            source="copernicus_marine",
            status="success",
            is_live=True,
            timestamp=now.isoformat(),
            sst_c=round(sst_c, 2) if sst_c is not None else None,
            chlorophyll_mg_m3=round(chlorophyll_mg_m3, 3) if chlorophyll_mg_m3 is not None else None,
            salinity_psu=round(salinity_psu, 2) if salinity_psu is not None else None,
            turbidity_fnu=round(turbidity_fnu, 2) if turbidity_fnu is not None else None,
            suspended_matter_mg_l=round(suspended_matter_mg_l, 2) if suspended_matter_mg_l is not None else None,
            current_speed_kmh=current_speed_kmh,
            current_direction_deg=current_direction_deg,
            productivity_index=productivity_index,
            turbidity_risk=turbidity_risk,
            advisory=advisory,
        )
        return self._store_cache(payload)

    def get_zone_observation(self, zone_id: str) -> SatelliteZoneResponse:
        zone = next((item for item in SEEDED_ZONES if item.id == zone_id), SEEDED_ZONES[0])
        return SatelliteZoneResponse(
            zone_id=zone.id,
            zone_label=zone.label,
            observation=self.get_point_observation(zone.center_lat, zone.center_lon),
        )


satellite_service = SatelliteService()
