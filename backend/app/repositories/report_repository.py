from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.db.database import get_db_connection
from app.models.report import CommunityReportCreate, CommunityReportSnapshot


class ReportRepository:
    def create_report(self, user_id: str, payload: CommunityReportCreate) -> None:
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO community_reports (
                    id, user_id, recorded_at, lat, lon, report_type, severity, species, note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    user_id,
                    datetime.now(UTC).isoformat(),
                    payload.lat,
                    payload.lon,
                    payload.report_type,
                    payload.severity,
                    payload.species,
                    payload.note,
                ),
            )

    def list_recent_reports(self, within_hours: int = 72) -> list[CommunityReportSnapshot]:
        since = (datetime.now(UTC) - timedelta(hours=within_hours)).isoformat()
        with get_db_connection() as connection:
            rows = connection.execute(
                """
                SELECT cr.id,
                       cr.user_id,
                       users.full_name AS reporter_name,
                       cr.lat,
                       cr.lon,
                       cr.report_type,
                       cr.severity,
                       cr.species,
                       cr.note,
                       cr.recorded_at
                FROM community_reports cr
                JOIN users ON users.id = cr.user_id
                WHERE cr.recorded_at >= ?
                ORDER BY cr.recorded_at DESC
                """,
                (since,),
            ).fetchall()

        return [
            CommunityReportSnapshot(
                id=row["id"],
                user_id=row["user_id"],
                reporter_name=row["reporter_name"],
                lat=row["lat"],
                lon=row["lon"],
                report_type=row["report_type"],
                severity=row["severity"],
                species=row["species"],
                note=row["note"],
                recorded_at=row["recorded_at"],
            )
            for row in rows
        ]


report_repository = ReportRepository()

