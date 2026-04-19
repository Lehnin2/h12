from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.db.database import get_db_connection
from app.models.admin import (
    AdminOverviewResponse,
    AdminPressureZone,
    AdminSourceHealth,
    AdminTerritoryMetric,
)
from app.models.profile import FishermanProfilePublic
from app.models.safety import SafetyEventResponse
from app.services.fleet_service import fleet_service
from app.services.mission_service import mission_service
from app.services.pollution_service import pollution_service
from app.services.report_service import report_service
from app.services.satellite_service import satellite_service
from app.services.weather_service import weather_service
from app.services.zone_engine import zone_engine


class AdminService:
    def _latest_timestamp(self, table: str, column: str = "created_at") -> str | None:
        with get_db_connection() as connection:
            row = connection.execute(f"SELECT MAX({column}) AS latest FROM {table}").fetchone()
        if row is None:
            return None
        return row["latest"]

    def _count_open_sos(self) -> int:
        with get_db_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM safety_events
                WHERE event_type = 'SOS' AND status = 'OPEN'
                """
            ).fetchone()
        return int(row["total"]) if row is not None else 0

    def _count_recent_mission_status(self, status: str, hours: int = 24) -> int:
        cutoff = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
        with get_db_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM mission_history
                WHERE requested_at >= ? AND departure_status = ?
                """,
                (cutoff, status),
            ).fetchone()
        return int(row["total"]) if row is not None else 0

    def _source_health(self) -> list[AdminSourceHealth]:
        weather = weather_service.get_port_forecast("ghannouch", hours=4)
        satellite = satellite_service.get_point_observation(33.952, 10.12)
        pollution = pollution_service.get_point_assessment(33.952, 10.12)
        freshness = mission_service._build_source_freshness(weather, satellite, pollution)
        return [
            AdminSourceHealth(
                source_key=item.source_key,
                freshness=item.freshness,
                detail=item.detail,
                age_minutes=item.age_minutes,
            )
            for item in freshness
        ]

    def _territorial_metrics(self) -> tuple[list[AdminTerritoryMetric], list[AdminSourceHealth]]:
        fleet = fleet_service.overview()
        recent_reports = report_service.list_recent_reports(within_hours=72)
        source_health = self._source_health()
        stale_sources = sum(1 for item in source_health if item.freshness in {"stale", "unknown"})
        stressed_zones = sum(1 for item in fleet.zone_loads if item.pressure_ratio >= 1.0)
        latest_mission = self._latest_timestamp("mission_history", "requested_at")
        latest_report = self._latest_timestamp("community_reports", "recorded_at")
        open_sos = self._count_open_sos()

        metrics = [
            AdminTerritoryMetric(
                label="Active boats",
                value=str(fleet.active_boats),
                tone="good" if fleet.active_boats else "neutral",
                detail="Latest active fleet positions inside the Gulf of Gabes corridor.",
            ),
            AdminTerritoryMetric(
                label="Open SOS",
                value=str(open_sos),
                tone="danger" if open_sos else "good",
                detail="Open safety incidents still needing relay or follow-up.",
            ),
            AdminTerritoryMetric(
                label="Stress zones",
                value=str(stressed_zones),
                tone="warn" if stressed_zones else "good",
                detail="Zones where predicted pressure is at or above capacity.",
            ),
            AdminTerritoryMetric(
                label="Reports 72h",
                value=str(len(recent_reports)),
                tone="neutral",
                detail="Recent community reports feeding territorial awareness.",
            ),
            AdminTerritoryMetric(
                label="NO_GO 24h",
                value=str(self._count_recent_mission_status("NO_GO", hours=24)),
                tone="warn",
                detail="Departure decisions held back by current mission intelligence.",
            ),
            AdminTerritoryMetric(
                label="Stale sources",
                value=str(stale_sources),
                tone="danger" if stale_sources else "good",
                detail=f"Latest mission {latest_mission or 'n/a'} · latest report {latest_report or 'n/a'}.",
            ),
        ]
        return metrics, source_health

    def overview(self, admin_user: FishermanProfilePublic) -> AdminOverviewResponse:
        fleet = fleet_service.overview()
        heatmap = zone_engine.build_heatmap("ghannouch", "poulpe")
        reports_feed = report_service.feed(within_hours=72)
        recent_missions = mission_service.history(limit=8).entries

        metrics, source_health = self._territorial_metrics()

        pressure_by_zone = {item.zone_id: item for item in fleet.zone_loads}
        pressure_zones = [
            AdminPressureZone(
                zone_id=zone.id,
                zone_label=zone.label,
                overall_score=zone.overall_score,
                color=zone.color,
                active_boats=pressure_by_zone[zone.id].active_boats if zone.id in pressure_by_zone else zone.active_boats,
                inbound_missions=pressure_by_zone[zone.id].recommended_boats if zone.id in pressure_by_zone else zone.recommended_boats,
                pressure_ratio=pressure_by_zone[zone.id].pressure_ratio if zone.id in pressure_by_zone else zone.saturation_ratio,
                pollution_index=zone.pollution_index,
                legal_status=zone.legal_status,
                advisory=zone.key_reason,
            )
            for zone in heatmap.zones[:5]
        ]

        with get_db_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, event_type, status, lat, lon, note, message_preview, created_at
                FROM safety_events
                ORDER BY created_at DESC
                LIMIT 6
                """
            ).fetchall()

        recent_safety_events = [
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

        return AdminOverviewResponse(
            generated_at=datetime.now(UTC).isoformat(),
            admin_email=admin_user.email,
            territorial_metrics=metrics,
            pressure_zones=pressure_zones,
            recent_safety_events=recent_safety_events,
            recent_reports=reports_feed.recent_reports[:6],
            recent_missions=recent_missions,
            source_health=source_health,
        )


admin_service = AdminService()
