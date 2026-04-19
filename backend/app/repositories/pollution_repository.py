from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.db.database import get_db_connection
from app.models.pollution import (
    PollutionObservationResponse,
    PollutionPlumeSnapshot,
    PollutionSourceSnapshot,
)


def _cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 3):.3f}:{round(lon, 3):.3f}"


class PollutionRepository:
    def list_sources(self) -> list[PollutionSourceSnapshot]:
        with get_db_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM pollution_sources ORDER BY base_severity DESC, name ASC"
            ).fetchall()
        return [
            PollutionSourceSnapshot(
                id=row["id"],
                name=row["name"],
                source_type=row["source_type"],
                lat=row["lat"],
                lon=row["lon"],
                base_severity=row["base_severity"],
                status=row["status"],
                notes=row["notes"],
            )
            for row in rows
        ]

    def get_recent_observation(
        self,
        lat: float,
        lon: float,
        max_age: timedelta,
    ) -> PollutionObservationResponse | None:
        cutoff = (datetime.now(UTC) - max_age).isoformat()
        with get_db_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM pollution_observations
                WHERE cache_key = ?
                  AND observed_at >= ?
                ORDER BY observed_at DESC
                LIMIT 1
                """,
                (_cache_key(lat, lon), cutoff),
            ).fetchone()
            if row is None:
                return None
        return PollutionObservationResponse(
            lat=row["lat"],
            lon=row["lon"],
            source=row["model_source"],
            status=row["status"],
            is_live=bool(row["is_live"]),
            observed_at=row["observed_at"],
            nearest_source_id=row["source_id"],
            nearest_source_name=row["source_name"],
            risk_score=row["risk_score"],
            contamination_index=row["contamination_index"],
            plume_direction_deg=row["plume_direction_deg"],
            plume_radius_km=row["plume_radius_km"],
            spread_speed_kmh=row["spread_speed_kmh"],
            advisory=row["advisory"],
        )

    def store_observation(self, payload: PollutionObservationResponse) -> None:
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO pollution_observations (
                    id, cache_key, lat, lon, source_id, source_name, model_source, status, is_live,
                    observed_at, risk_score, contamination_index, plume_direction_deg, plume_radius_km,
                    spread_speed_kmh, advisory
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    _cache_key(payload.lat, payload.lon),
                    payload.lat,
                    payload.lon,
                    payload.nearest_source_id,
                    payload.nearest_source_name,
                    payload.source,
                    payload.status,
                    1 if payload.is_live else 0,
                    payload.observed_at,
                    payload.risk_score,
                    payload.contamination_index,
                    payload.plume_direction_deg,
                    payload.plume_radius_km,
                    payload.spread_speed_kmh,
                    payload.advisory,
                ),
            )

    def store_plume_snapshot(self, payload: PollutionPlumeSnapshot) -> None:
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO pollution_plume_history (
                    id, source_id, source_name, center_lat, center_lon, observed_at,
                    plume_direction_deg, plume_radius_km, spread_speed_kmh, core_risk, geometry_hint_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    payload.source_id,
                    payload.source_name,
                    payload.center_lat,
                    payload.center_lon,
                    payload.observed_at,
                    payload.plume_direction_deg,
                    payload.plume_radius_km,
                    payload.spread_speed_kmh,
                    payload.core_risk,
                    payload.geometry_hint_json,
                ),
            )

    def list_recent_plumes(
        self,
        within_hours: int = 48,
        limit: int = 24,
    ) -> list[PollutionPlumeSnapshot]:
        cutoff = (datetime.now(UTC) - timedelta(hours=within_hours)).isoformat()
        with get_db_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM pollution_plume_history
                WHERE observed_at >= ?
                ORDER BY observed_at DESC
                LIMIT ?
                """,
                (cutoff, limit),
            ).fetchall()
        return [
            PollutionPlumeSnapshot(
                source_id=row["source_id"],
                source_name=row["source_name"],
                center_lat=row["center_lat"],
                center_lon=row["center_lon"],
                observed_at=row["observed_at"],
                plume_direction_deg=row["plume_direction_deg"],
                plume_radius_km=row["plume_radius_km"],
                spread_speed_kmh=row["spread_speed_kmh"],
                core_risk=row["core_risk"],
                geometry_hint_json=row["geometry_hint_json"],
            )
            for row in rows
        ]


pollution_repository = PollutionRepository()

