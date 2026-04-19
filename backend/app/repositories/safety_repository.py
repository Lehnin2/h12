from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from app.db.database import get_db_connection
from app.models.safety import SafetyEventResponse


class SafetyRepository:
    def create_event(
        self,
        user_id: str,
        event_type: str,
        status: str,
        lat: float,
        lon: float,
        note: str | None,
        message_preview: str,
        payload: dict[str, object],
    ) -> SafetyEventResponse:
        event = SafetyEventResponse(
            id=str(uuid4()),
            event_type=event_type,
            status=status,
            lat=lat,
            lon=lon,
            note=note,
            message_preview=message_preview,
            created_at=datetime.now(UTC).isoformat(),
        )
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO safety_events (
                    id, user_id, event_type, status, lat, lon, note, message_preview, payload_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    user_id,
                    event_type,
                    status,
                    lat,
                    lon,
                    note,
                    message_preview,
                    json.dumps(payload),
                    event.created_at,
                ),
            )
        return event

    def list_recent_events(self, user_id: str, limit: int = 20) -> list[SafetyEventResponse]:
        with get_db_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, event_type, status, lat, lon, note, message_preview, created_at
                FROM safety_events
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [
            SafetyEventResponse(
                id=row["id"],
                event_type=row["event_type"],
                status=row["status"],
                lat=row["lat"],
                lon=row["lon"],
                note=row["note"],
                message_preview=row["message_preview"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def latest_check_in(self, user_id: str) -> SafetyEventResponse | None:
        with get_db_connection() as connection:
            row = connection.execute(
                """
                SELECT id, event_type, status, lat, lon, note, message_preview, created_at
                FROM safety_events
                WHERE user_id = ? AND event_type = 'CHECK_IN'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return SafetyEventResponse(
            id=row["id"],
            event_type=row["event_type"],
            status=row["status"],
            lat=row["lat"],
            lon=row["lon"],
            note=row["note"],
            message_preview=row["message_preview"],
            created_at=row["created_at"],
        )

    def open_incidents_count(self, user_id: str) -> int:
        with get_db_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM safety_events
                WHERE user_id = ?
                  AND event_type = 'SOS'
                  AND status = 'OPEN'
                """,
                (user_id,),
            ).fetchone()
        return int(row["total"]) if row is not None else 0


safety_repository = SafetyRepository()
