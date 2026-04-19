from __future__ import annotations

from collections import defaultdict

from app.domain.zone_seed import SEEDED_ZONES
from app.models.report import (
    CommunityReportCreate,
    CommunityReportFeedResponse,
    CommunityReportSnapshot,
    ZoneReportSummary,
)
from app.repositories.report_repository import report_repository
from app.services.utils import haversine_km


class ReportService:
    def submit_report(self, user_id: str, payload: CommunityReportCreate) -> None:
        report_repository.create_report(user_id, payload)

    def _nearest_zone(self, lat: float, lon: float) -> tuple[str | None, str | None]:
        best_zone = None
        best_distance = None
        for zone in SEEDED_ZONES:
            distance = haversine_km(lat, lon, zone.center_lat, zone.center_lon)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_zone = zone
        if best_zone is None or best_distance is None or best_distance > 22:
            return None, None
        return best_zone.id, best_zone.label

    def list_recent_reports(self, within_hours: int = 72) -> list[CommunityReportSnapshot]:
        reports = report_repository.list_recent_reports(within_hours)
        enriched: list[CommunityReportSnapshot] = []
        for report in reports:
            zone_id, zone_label = self._nearest_zone(report.lat, report.lon)
            enriched.append(
                report.model_copy(
                    update={
                        "zone_id": zone_id,
                        "zone_label": zone_label,
                    }
                )
            )
        return enriched

    def list_nearby_reports(
        self,
        lat: float,
        lon: float,
        radius_km: float = 20.0,
        within_hours: int = 72,
    ) -> list[CommunityReportSnapshot]:
        recent_reports = self.list_recent_reports(within_hours)
        return [
            report
            for report in recent_reports
            if haversine_km(lat, lon, report.lat, report.lon) <= radius_km
        ]

    def compute_zone_summaries(self, within_hours: int = 72) -> dict[str, ZoneReportSummary]:
        grouped: dict[str, list[CommunityReportSnapshot]] = defaultdict(list)
        for report in self.list_recent_reports(within_hours):
            if report.zone_id is not None:
                grouped[report.zone_id].append(report)

        summaries: dict[str, ZoneReportSummary] = {}
        for zone in SEEDED_ZONES:
            reports = grouped.get(zone.id, [])
            catch_reports = sum(1 for report in reports if report.report_type == "catch")
            pollution_reports = sum(1 for report in reports if report.report_type == "pollution")
            hazard_reports = sum(1 for report in reports if report.report_type == "hazard")
            illegal_activity_reports = sum(
                1 for report in reports if report.report_type == "illegal_activity"
            )
            current_reports = sum(1 for report in reports if report.report_type == "current")

            productivity_signal = round(min(catch_reports * 0.28, 1.0), 2)
            risk_signal = round(
                min(
                    pollution_reports * 0.42
                    + hazard_reports * 0.30
                    + illegal_activity_reports * 0.18
                    + current_reports * 0.12,
                    1.0,
                ),
                2,
            )

            advisory = None
            if pollution_reports:
                advisory = "Community reports indicate possible polluted water or suspicious fish quality."
            elif hazard_reports:
                advisory = "Community reports indicate navigation or equipment hazards in this zone."
            elif illegal_activity_reports:
                advisory = "Community reports indicate illegal fishing pressure nearby."
            elif catch_reports:
                advisory = "Recent catches reported by nearby fishermen improve confidence in this zone."
            elif current_reports:
                advisory = "Recent current reports suggest moderate sea handling caution."

            summaries[zone.id] = ZoneReportSummary(
                zone_id=zone.id,
                zone_label=zone.label,
                total_reports=len(reports),
                catch_reports=catch_reports,
                pollution_reports=pollution_reports,
                hazard_reports=hazard_reports,
                illegal_activity_reports=illegal_activity_reports,
                current_reports=current_reports,
                productivity_signal=productivity_signal,
                risk_signal=risk_signal,
                advisory=advisory,
            )
        return summaries

    def zone_summary(self, zone_id: str, within_hours: int = 72) -> ZoneReportSummary:
        summaries = self.compute_zone_summaries(within_hours)
        return summaries[zone_id]

    def feed(self, within_hours: int = 72) -> CommunityReportFeedResponse:
        summaries = self.compute_zone_summaries(within_hours)
        return CommunityReportFeedResponse(
            recent_reports=self.list_recent_reports(within_hours),
            zone_summaries=list(summaries.values()),
        )


report_service = ReportService()

