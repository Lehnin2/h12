from __future__ import annotations

from datetime import UTC, datetime

from app.models.profile import FishermanProfilePublic
from app.models.mission import (
    MissionBriefingResponse,
    MissionDepartureDecision,
    MissionHistoryResponse,
    MissionSourceFreshness,
)
from app.repositories.mission_repository import mission_repository
from app.services.fleet_service import fleet_service
from app.services.pollution_service import pollution_service
from app.services.satellite_service import satellite_service
from app.services.lunar_service import lunar_service
from app.services.regulatory_service import regulatory_service
from app.services.routing_service import routing_service
from app.services.safety_service import safety_service
from app.services.weather_service import weather_service
from app.services.zone_engine import zone_engine


class MissionService:
    def _age_minutes(self, observed_at: str | None) -> int | None:
        if observed_at is None:
            return None
        observed = datetime.fromisoformat(observed_at)
        return max(0, round((datetime.now(UTC) - observed).total_seconds() / 60))

    def _freshness_label(
        self,
        age_minutes: int | None,
        *,
        is_live: bool,
        static: bool = False,
        fresh_limit: int = 90,
        aging_limit: int = 300,
    ) -> str:
        if static:
            return "static"
        if age_minutes is None:
            return "unknown"
        if age_minutes <= fresh_limit:
            return "fresh" if is_live else "fresh_cached"
        if age_minutes <= aging_limit:
            return "aging"
        return "stale"

    def _build_source_freshness(
        self,
        weather,
        satellite,
        pollution,
    ) -> list[MissionSourceFreshness]:
        fleet_observed_at, fleet_is_current = fleet_service.freshness_snapshot()
        fleet_age = self._age_minutes(fleet_observed_at)
        weather_age = self._age_minutes(weather.current.timestamp)
        satellite_age = self._age_minutes(satellite.timestamp)
        pollution_age = self._age_minutes(pollution.observed_at)
        return [
            MissionSourceFreshness(
                source_key="weather",
                source_name=weather.source,
                freshness=self._freshness_label(weather_age, is_live=weather.is_live),
                age_minutes=weather_age,
                observed_at=weather.current.timestamp,
                is_live=weather.is_live,
                detail="Marine forecast driving route readiness and departure gating.",
            ),
            MissionSourceFreshness(
                source_key="satellite",
                source_name=satellite.source,
                freshness=self._freshness_label(satellite_age, is_live=satellite.is_live, fresh_limit=180, aging_limit=720),
                age_minutes=satellite_age,
                observed_at=satellite.timestamp,
                is_live=satellite.is_live,
                detail="Copernicus SST, chlorophyll, and surface current layer for productivity scoring.",
            ),
            MissionSourceFreshness(
                source_key="pollution",
                source_name=pollution.source,
                freshness=self._freshness_label(pollution_age, is_live=pollution.is_live, fresh_limit=120, aging_limit=480),
                age_minutes=pollution_age,
                observed_at=pollution.observed_at,
                is_live=pollution.is_live,
                detail="Hybrid plume model blended with nearby reports and marine conditions.",
            ),
            MissionSourceFreshness(
                source_key="fleet",
                source_name="fleet_positioning",
                freshness=self._freshness_label(fleet_age, is_live=fleet_is_current, fresh_limit=60, aging_limit=240),
                age_minutes=fleet_age,
                observed_at=fleet_observed_at,
                is_live=fleet_is_current,
                detail="Recent boat positions plus short-term mission reservations for anti-saturation balancing.",
            ),
            MissionSourceFreshness(
                source_key="regulation",
                source_name="guardian_regulatory_ruleset",
                freshness=self._freshness_label(None, is_live=False, static=True),
                age_minutes=None,
                observed_at=None,
                is_live=False,
                detail="Protected areas, seasonal closures, gear constraints, and license restrictions.",
            ),
            MissionSourceFreshness(
                source_key="bathymetry",
                source_name="carte_marine_tunisie_offline",
                freshness=self._freshness_label(None, is_live=False, static=True),
                age_minutes=None,
                observed_at=None,
                is_live=False,
                detail="Offline depth dataset used for route and zone depth compatibility.",
            ),
        ]

    def _build_departure_decision(
        self,
        recommendation,
        route,
        weather,
        regulation,
        safety,
    ) -> MissionDepartureDecision:
        reasons: list[str] = []
        actions: list[str] = list(safety.recommended_checks[:3])

        if recommendation.recommendation_status != "ACTIONABLE":
            reasons.append(recommendation.advisory)
            if "Wait for a stronger legal, environmental, and productivity window." not in actions:
                actions.append("Wait for a stronger legal, environmental, and productivity window.")

        if regulation.overall_status == "PROHIBITED":
            reasons.extend(regulation.violations[:2])
        elif regulation.overall_status == "RESTRICTED":
            reasons.extend(regulation.advisories[:2])

        reasons.extend(safety.blocking_reasons[:2])

        if not reasons:
            reasons.append(
                f"Sea state is {weather.current.condition} and route risk is {route.route_risk_level.lower()}."
            )

        if recommendation.recommendation_status != "ACTIONABLE":
            summary = "Departure should be held. No zone currently clears the minimum safe threshold."
        elif safety.departure_status == "NO_GO":
            summary = "Departure should be delayed. Current legal, weather, or route conditions are not safe enough."
        elif safety.departure_status == "CAUTION":
            summary = "Departure is possible with caution. Keep the mission short and conservative."
        else:
            summary = "Departure window is acceptable for the recommended zone with current route and safety settings."

        if route.route_readiness == "NO_GO" and "Wait for a calmer route weather window." not in actions:
            actions.append("Wait for a calmer route weather window.")
        if weather.current.condition == "moderate" and "Prefer a shorter nearby zone if conditions worsen." not in actions:
            actions.append("Prefer a shorter nearby zone if conditions worsen.")
        if regulation.overall_status == "RESTRICTED" and "Confirm authorized gear and target species before departure." not in actions:
            actions.append("Confirm authorized gear and target species before departure.")

        return MissionDepartureDecision(
            status="NO_GO" if recommendation.recommendation_status != "ACTIONABLE" else safety.departure_status,
            score=min(safety.safety_score, 32) if recommendation.recommendation_status != "ACTIONABLE" else safety.safety_score,
            summary=summary,
            reasons=reasons[:4],
            actions=actions[:4],
        )

    def _compose_briefing(
        self,
        departure_port: str,
        species: str,
        profile: FishermanProfilePublic | None = None,
    ) -> MissionBriefingResponse:
        if profile is not None:
            heatmap = zone_engine.build_heatmap(profile.home_port, species, profile)
            recommendation = zone_engine.recommend(profile.home_port, species, profile)
            regulation = regulatory_service.assess_for_profile(
                recommendation.best_zone.center_lat,
                recommendation.best_zone.center_lon,
                profile,
                species,
            )
            route = routing_service.optimize(profile.home_port, recommendation.best_zone.id, profile)
            departure_port = profile.home_port
        else:
            heatmap = zone_engine.build_heatmap(departure_port, species)
            recommendation = zone_engine.recommend(departure_port, species)
            regulation = regulatory_service.assess(
                recommendation.best_zone.center_lat,
                recommendation.best_zone.center_lon,
                species=species,
            )
            route = routing_service.optimize(departure_port, recommendation.best_zone.id)

        satellite = satellite_service.get_point_observation(
            recommendation.best_zone.center_lat,
            recommendation.best_zone.center_lon,
        )
        weather = weather_service.get_point_forecast(
            recommendation.best_zone.center_lat,
            recommendation.best_zone.center_lon,
        )
        pollution = pollution_service.get_point_assessment(
            recommendation.best_zone.center_lat,
            recommendation.best_zone.center_lon,
        )
        lunar = lunar_service.get_today(species)
        safety = safety_service.get_status(departure_port, weather, route, regulation, profile)
        departure_decision = self._build_departure_decision(recommendation, route, weather, regulation, safety)
        source_freshness = self._build_source_freshness(weather, satellite, pollution)
        briefing = MissionBriefingResponse(
            departure_port=recommendation.departure_port,
            selected_species=species,
            heatmap=heatmap,
            recommendation=recommendation,
            regulation=regulation,
            route=route,
            satellite=satellite,
            weather=weather,
            lunar=lunar,
            safety=safety,
            departure_decision=departure_decision,
            source_freshness=source_freshness,
        )
        mission_repository.create_history_entry(
            briefing=briefing,
            source_freshness=source_freshness,
            user_id=profile.id if profile is not None else None,
        )
        return briefing

    def build_briefing(self, departure_port: str, species: str) -> MissionBriefingResponse:
        return self._compose_briefing(departure_port, species)

    def build_briefing_for_user(self, profile: FishermanProfilePublic) -> MissionBriefingResponse:
        selected_species = profile.target_species[0] if profile.target_species else "poulpe"
        return self._compose_briefing(profile.home_port, selected_species, profile)

    def history(self, limit: int = 20) -> MissionHistoryResponse:
        return MissionHistoryResponse(entries=mission_repository.list_history(limit=limit))

    def history_for_user(self, user_id: str, limit: int = 20) -> MissionHistoryResponse:
        return MissionHistoryResponse(entries=mission_repository.list_history(limit=limit, user_id=user_id))


mission_service = MissionService()
