from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.db.database import get_db_connection
from app.models.mission import MissionBriefingResponse, MissionHistoryEntry, MissionSourceFreshness


class MissionRepository:
    def create_history_entry(
        self,
        briefing: MissionBriefingResponse,
        source_freshness: list[MissionSourceFreshness],
        user_id: str | None = None,
    ) -> None:
        requested_at = datetime.now(UTC).isoformat()
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO mission_history (
                    id,
                    user_id,
                    requested_at,
                    departure_port,
                    selected_species,
                    recommended_zone_id,
                    recommended_zone_label,
                    departure_status,
                    mission_score,
                    recommendation_json,
                    source_freshness_json,
                    briefing_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    user_id,
                    requested_at,
                    briefing.departure_port,
                    briefing.selected_species,
                    briefing.recommendation.best_zone.id,
                    briefing.recommendation.best_zone.label,
                    briefing.departure_decision.status,
                    briefing.departure_decision.score,
                    json.dumps(briefing.recommendation.model_dump()),
                    json.dumps([item.model_dump() for item in source_freshness]),
                    json.dumps(briefing.model_dump()),
                ),
            )

    def list_history(
        self,
        limit: int = 20,
        user_id: str | None = None,
    ) -> list[MissionHistoryEntry]:
        query = """
            SELECT id,
                   requested_at,
                   departure_port,
                   selected_species,
                   recommended_zone_id,
                   recommended_zone_label,
                   departure_status,
                   mission_score
            FROM mission_history
        """
        params: list[object] = []
        if user_id is not None:
            query += " WHERE user_id = ?"
            params.append(user_id)
        query += " ORDER BY requested_at DESC LIMIT ?"
        params.append(limit)

        with get_db_connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()

        return [
            MissionHistoryEntry(
                id=row["id"],
                requested_at=row["requested_at"],
                departure_port=row["departure_port"],
                selected_species=row["selected_species"],
                recommended_zone_id=row["recommended_zone_id"],
                recommended_zone_label=row["recommended_zone_label"],
                departure_status=row["departure_status"],
                mission_score=row["mission_score"],
            )
            for row in rows
        ]

    def count_recent_zone_recommendations(self, within_minutes: int = 120) -> dict[str, int]:
        cutoff = (datetime.now(UTC) - timedelta(minutes=within_minutes)).isoformat()
        with get_db_connection() as connection:
            rows = connection.execute(
                """
                SELECT recommended_zone_id, COUNT(*) AS total
                FROM mission_history
                WHERE requested_at >= ?
                GROUP BY recommended_zone_id
                """,
                (cutoff,),
            ).fetchall()
        return {row["recommended_zone_id"]: row["total"] for row in rows}


mission_repository = MissionRepository()
