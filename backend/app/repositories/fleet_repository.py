from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.db.database import get_db_connection
from app.models.fleet import FleetPositionCreate, FleetPositionSnapshot


class FleetRepository:
    def create_position(self, user_id: str, payload: FleetPositionCreate) -> None:
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO fleet_positions (
                    id, user_id, recorded_at, lat, lon, speed_kmh, heading_deg, is_at_sea, note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    user_id,
                    datetime.now(UTC).isoformat(),
                    payload.lat,
                    payload.lon,
                    payload.speed_kmh,
                    payload.heading_deg,
                    1 if payload.is_at_sea else 0,
                    payload.note,
                ),
            )

    def list_active_positions(self, within_minutes: int = 240) -> list[FleetPositionSnapshot]:
        since = (datetime.now(UTC) - timedelta(minutes=within_minutes)).isoformat()
        with get_db_connection() as connection:
            rows = connection.execute(
                """
                SELECT fp.user_id,
                       users.full_name,
                       users.boat_name,
                       fp.lat,
                       fp.lon,
                       fp.speed_kmh,
                       fp.heading_deg,
                       fp.recorded_at,
                       fp.is_at_sea
                FROM fleet_positions fp
                JOIN (
                    SELECT user_id, MAX(recorded_at) AS latest_recorded_at
                    FROM fleet_positions
                    GROUP BY user_id
                ) latest
                  ON latest.user_id = fp.user_id
                 AND latest.latest_recorded_at = fp.recorded_at
                JOIN users ON users.id = fp.user_id
                WHERE fp.recorded_at >= ?
                ORDER BY fp.recorded_at DESC
                """,
                (since,),
            ).fetchall()

        return [
            FleetPositionSnapshot(
                user_id=row["user_id"],
                full_name=row["full_name"],
                boat_name=row["boat_name"],
                lat=row["lat"],
                lon=row["lon"],
                speed_kmh=row["speed_kmh"],
                heading_deg=row["heading_deg"],
                recorded_at=row["recorded_at"],
                is_at_sea=bool(row["is_at_sea"]),
            )
            for row in rows
        ]

    def latest_position_timestamp(self, within_minutes: int = 240) -> str | None:
        since = (datetime.now(UTC) - timedelta(minutes=within_minutes)).isoformat()
        with get_db_connection() as connection:
            row = connection.execute(
                """
                SELECT MAX(recorded_at) AS latest_recorded_at
                FROM fleet_positions
                WHERE recorded_at >= ?
                """,
                (since,),
            ).fetchone()
        if row is None:
            return None
        return row["latest_recorded_at"]


fleet_repository = FleetRepository()
