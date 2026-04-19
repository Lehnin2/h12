from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.db.database import get_db_connection
from app.models.satellite import SatelliteObservationResponse


def _cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 3):.3f}:{round(lon, 3):.3f}"


class SatelliteRepository:
    def get_recent_observation(
        self,
        lat: float,
        lon: float,
        max_age: timedelta,
    ) -> SatelliteObservationResponse | None:
        cutoff = (datetime.now(UTC) - max_age).isoformat()
        with get_db_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM satellite_observations
                WHERE cache_key = ?
                  AND created_at >= ?
                """,
                (_cache_key(lat, lon), cutoff),
            ).fetchone()
            if row is None:
                return None
            return SatelliteObservationResponse(
                lat=row["lat"],
                lon=row["lon"],
                source=row["source"],
                status=row["status"],
                is_live=bool(row["is_live"]),
                timestamp=row["observation_timestamp"],
                sst_c=row["sst_c"],
                chlorophyll_mg_m3=row["chlorophyll_mg_m3"],
                salinity_psu=row["salinity_psu"],
                turbidity_fnu=row["turbidity_fnu"],
                suspended_matter_mg_l=row["suspended_matter_mg_l"],
                current_speed_kmh=row["current_speed_kmh"],
                current_direction_deg=row["current_direction_deg"],
                productivity_index=row["productivity_index"],
                turbidity_risk=row["turbidity_risk"],
                advisory=row["advisory"],
            )

    def upsert_observation(self, payload: SatelliteObservationResponse) -> None:
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO satellite_observations (
                    cache_key,
                    lat,
                    lon,
                    source,
                    status,
                    is_live,
                    observation_timestamp,
                    sst_c,
                    chlorophyll_mg_m3,
                    salinity_psu,
                    turbidity_fnu,
                    suspended_matter_mg_l,
                    current_speed_kmh,
                    current_direction_deg,
                    productivity_index,
                    turbidity_risk,
                    advisory,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    lat = excluded.lat,
                    lon = excluded.lon,
                    source = excluded.source,
                    status = excluded.status,
                    is_live = excluded.is_live,
                    observation_timestamp = excluded.observation_timestamp,
                    sst_c = excluded.sst_c,
                    chlorophyll_mg_m3 = excluded.chlorophyll_mg_m3,
                    salinity_psu = excluded.salinity_psu,
                    turbidity_fnu = excluded.turbidity_fnu,
                    suspended_matter_mg_l = excluded.suspended_matter_mg_l,
                    current_speed_kmh = excluded.current_speed_kmh,
                    current_direction_deg = excluded.current_direction_deg,
                    productivity_index = excluded.productivity_index,
                    turbidity_risk = excluded.turbidity_risk,
                    advisory = excluded.advisory,
                    created_at = excluded.created_at
                """,
                (
                    _cache_key(payload.lat, payload.lon),
                    payload.lat,
                    payload.lon,
                    payload.source,
                    payload.status,
                    1 if payload.is_live else 0,
                    payload.timestamp,
                    payload.sst_c,
                    payload.chlorophyll_mg_m3,
                    payload.salinity_psu,
                    payload.turbidity_fnu,
                    payload.suspended_matter_mg_l,
                    payload.current_speed_kmh,
                    payload.current_direction_deg,
                    payload.productivity_index,
                    payload.turbidity_risk,
                    payload.advisory,
                    datetime.now(UTC).isoformat(),
                ),
            )


satellite_repository = SatelliteRepository()
