from app.models.profile import FishermanProfilePublic
from app.domain.species import SPECIES_PROFILES
from app.domain.zone_seed import SEEDED_ZONES
from app.models.zone import HeatmapResponse, RecommendationResponse, ZoneCard, ZoneSeed
from app.services.bathymetry_service import bathymetry_service
from app.services.catalog_service import catalog_service
from app.services.fleet_service import fleet_service
from app.services.lunar_service import lunar_service
from app.services.pollution_service import pollution_service
from app.services.report_service import report_service
from app.services.regulatory_service import regulatory_service
from app.services.satellite_service import satellite_service
from app.services.utils import haversine_km
from app.services.weather_service import weather_service


class ZoneEngine:
    recommendation_threshold = 58.0
    legend = {
        "GREEN": "Legal, productive, low pollution, low saturation",
        "ORANGE": "Usable but with moderate trade-offs",
        "RED": "Unsafe or too weak economically for departure today",
        "BLACK": "Protected or legally closed",
    }

    def _species_fit(self, seed: ZoneSeed, species: str) -> float:
        profile = SPECIES_PROFILES.get(species, {})
        depth_min = float(profile.get("preferred_depth_min", 10.0))
        depth_max = float(profile.get("preferred_depth_max", 25.0))
        if depth_min <= seed.depth_m <= depth_max:
            return 1.0
        gap = min(abs(seed.depth_m - depth_min), abs(seed.depth_m - depth_max))
        return max(0.55, 1.0 - gap / 50)

    def _slope_fit(self, slope_deg: float, species: str) -> float:
        if species in {"poulpe", "rouget", "crevette_royale"}:
            ideal_min, ideal_max = 1.5, 9.0
        else:
            ideal_min, ideal_max = 0.5, 6.0

        if ideal_min <= slope_deg <= ideal_max:
            return 1.0
        gap = min(abs(slope_deg - ideal_min), abs(slope_deg - ideal_max))
        return max(0.6, 1.0 - gap / 18)

    def _salinity_fit(self, salinity_psu: float | None) -> float:
        if salinity_psu is None:
            return 0.84
        if 37.1 <= salinity_psu <= 39.0:
            return 1.0
        gap = min(abs(salinity_psu - 37.1), abs(salinity_psu - 39.0))
        return max(0.58, 1.0 - gap / 3.2)

    def _color(self, score: float, legal_status: str) -> str:
        if legal_status in {"PROTECTED", "CLOSED", "PROHIBITED"}:
            return "BLACK"
        if score >= 74:
            return "GREEN"
        if score >= 52:
            return "ORANGE"
        return "RED"

    def _reason(self, seed: ZoneSeed, score: float, species: str) -> str:
        if seed.legal_status in {"PROTECTED", "CLOSED"}:
            return "Protected area or seasonal closure"
        if seed.pollution_risk > 0.6:
            return "Pollution plume influence is too strong"
        if seed.fleet_load > 0.55:
            return "Zone is productive but already crowded"
        if species in seed.recommended_species:
            return f"Strong match for {species.replace('_', ' ')} with stable sea state"
        return "Balanced option with legal access and manageable route cost"

    def _distance_penalty(
        self,
        distance_km: float,
        profile: FishermanProfilePublic | None,
    ) -> float:
        base_range = 24.0
        if profile is not None:
            if profile.license_type == "artisanal":
                base_range = max(14.0, profile.fuel_capacity_l / 3.2)
            elif profile.license_type == "côtier":
                base_range = max(20.0, profile.fuel_capacity_l / 2.8)
            else:
                base_range = max(28.0, profile.fuel_capacity_l / 2.4)
        return min(distance_km / base_range, 1.0)

    def _score_zone(
        self,
        seed: ZoneSeed,
        departure_port: str,
        species: str,
        profile: FishermanProfilePublic | None = None,
        dynamic_saturation: float = 0.0,
        active_boats: int = 0,
        recommended_boats: int = 0,
        report_productivity_signal: float = 0.0,
        report_risk_signal: float = 0.0,
        community_reports: int = 0,
        report_advisory: str | None = None,
        marine_condition: str = "calm",
        marine_fishing_score: int = 70,
        weather_advisory: str | None = None,
        weather_source: str = "seeded_fallback",
        weather_live: bool = False,
        satellite_source: str = "copernicus_fallback_seeded",
        satellite_live: bool = False,
        sst_c: float | None = None,
        chlorophyll_mg_m3: float | None = None,
        salinity_psu: float | None = None,
        turbidity_fnu: float | None = None,
        satellite_current_speed_kmh: float | None = None,
        satellite_productivity_index: int = 55,
        satellite_advisory: str | None = None,
        pollution_source_name: str | None = None,
        pollution_data_live: bool = False,
        pollution_index: int = 0,
        pollution_advisory: str | None = None,
        dynamic_pollution_risk: float | None = None,
    ) -> ZoneCard:
        port = catalog_service.get_port(departure_port)
        distance_km = haversine_km(port.lat, port.lon, seed.center_lat, seed.center_lon)
        distance_penalty = self._distance_penalty(distance_km, profile)
        lunar_factor = lunar_service.lunar_factor(species)
        depth_lookup = bathymetry_service.depth_at(seed.center_lat, seed.center_lon)
        effective_depth = depth_lookup.depth_m if depth_lookup.depth_m > 0 else seed.depth_m
        slope_deg = depth_lookup.slope_deg
        effective_seed = seed.model_copy(update={"depth_m": effective_depth})
        if dynamic_pollution_risk is not None:
            blended_pollution = round(
                min(max(effective_seed.pollution_risk * 0.4 + dynamic_pollution_risk * 0.6, 0.0), 1.0),
                2,
            )
            effective_seed = effective_seed.model_copy(update={"pollution_risk": blended_pollution})
        if chlorophyll_mg_m3 is not None:
            normalized_chlorophyll = min(max(chlorophyll_mg_m3 / 2.4, 0.0), 1.0)
            effective_seed = effective_seed.model_copy(
                update={
                    "chlorophyll": round(normalized_chlorophyll, 2),
                    "current_speed": round(
                        (satellite_current_speed_kmh or effective_seed.current_speed * 3.6) / 3.6,
                        2,
                    ),
                }
            )
        if turbidity_fnu is not None:
            if turbidity_fnu >= 12:
                effective_seed = effective_seed.model_copy(
                    update={"pollution_risk": round(min(effective_seed.pollution_risk + 0.18, 1.0), 2)}
                )
            elif turbidity_fnu >= 5:
                effective_seed = effective_seed.model_copy(
                    update={"pollution_risk": round(min(effective_seed.pollution_risk + 0.08, 1.0), 2)}
                )
        species_fit = self._species_fit(effective_seed, species)
        slope_fit = self._slope_fit(slope_deg, species)
        salinity_fit = self._salinity_fit(salinity_psu)
        gear_bonus = 1.0
        regulation = None
        if profile is not None and species in effective_seed.recommended_species:
            if "ligne" in profile.fishing_gears or "palangre" in profile.fishing_gears:
                gear_bonus += 0.04
            if "charfia" in profile.fishing_gears and effective_depth < 16:
                gear_bonus += 0.03
            regulation = regulatory_service.assess_for_profile(
                effective_seed.center_lat,
                effective_seed.center_lon,
                profile,
                species,
            )
        elif profile is None:
            regulation = regulatory_service.assess(
                effective_seed.center_lat,
                effective_seed.center_lon,
                species=species,
            )

        fish_score = (
            48
            + effective_seed.chlorophyll * 30
            + species_fit * 16
            + slope_fit * 8
            + salinity_fit * 6
            + (1 - min(effective_seed.wave_height / 2.6, 1.0)) * 8
            + report_productivity_signal * 8
            + (marine_fishing_score / 100) * 12
            + (satellite_productivity_index / 100) * 10
        ) * gear_bonus
        fish_score = min(fish_score, 100)

        if effective_seed.legal_status in {"PROTECTED", "CLOSED"}:
            overall_score = 0.0
        else:
            effective_fleet_load = min(
                1.0,
                effective_seed.fleet_load * 0.35 + dynamic_saturation * 0.65,
            )
            overall_score = (
                fish_score * 0.46
                + (1 - effective_seed.pollution_risk) * 24
                + (1 - effective_fleet_load) * 18
                + (1 - distance_penalty) * 12
            ) * lunar_factor / 1.05
            effective_seed = effective_seed.model_copy(update={"fleet_load": round(effective_fleet_load, 2)})
            overall_score += report_productivity_signal * 6
            overall_score -= report_risk_signal * 14
            overall_score += (marine_fishing_score / 100) * 10
            overall_score += (satellite_productivity_index / 100) * 9
            if turbidity_fnu is not None:
                overall_score -= min(max(turbidity_fnu - 3.0, 0.0) * 1.6, 18)

        if regulation is not None:
            if regulation.overall_status == "PROHIBITED":
                overall_score = 0.0
                effective_seed = effective_seed.model_copy(update={"legal_status": "PROHIBITED"})
            elif regulation.overall_status == "RESTRICTED":
                overall_score *= 0.82

        if dynamic_saturation >= 1.0 and effective_seed.legal_status not in {"PROTECTED", "PROHIBITED"}:
            overall_score *= 0.72
        if marine_condition == "rough" and effective_seed.legal_status not in {"PROTECTED", "PROHIBITED"}:
            overall_score *= 0.68
        elif marine_condition == "moderate" and effective_seed.legal_status not in {"PROTECTED", "PROHIBITED"}:
            overall_score *= 0.91

        overall_score = round(max(0.0, min(overall_score, 100.0)), 1)
        color = self._color(overall_score, effective_seed.legal_status)
        confidence = round(
            0.56
            + effective_seed.chlorophyll * 0.16
            + (1 - effective_seed.pollution_risk) * 0.12
            + (marine_fishing_score / 100) * 0.08,
            2,
        )

        return ZoneCard(
            id=effective_seed.id,
            label=effective_seed.label,
            center_lat=effective_seed.center_lat,
            center_lon=effective_seed.center_lon,
            depth_m=effective_depth,
            slope_deg=slope_deg,
            legal_status=effective_seed.legal_status,
            pollution_risk=effective_seed.pollution_risk,
            pollution_index=pollution_index,
            pollution_source=pollution_source_name,
            pollution_data_live=pollution_data_live,
            fleet_load=effective_seed.fleet_load,
            fish_score=round(fish_score, 1),
            overall_score=overall_score,
            confidence=min(confidence, 0.96),
            color=color,
            satellite_source=satellite_source,
            satellite_live=satellite_live,
            sst_c=sst_c,
            chlorophyll_mg_m3=chlorophyll_mg_m3,
            salinity_psu=salinity_psu,
            turbidity_fnu=turbidity_fnu,
            satellite_current_speed_kmh=satellite_current_speed_kmh,
            satellite_productivity_index=satellite_productivity_index,
            marine_condition=marine_condition,
            marine_fishing_score=marine_fishing_score,
            weather_source=weather_source,
            weather_live=weather_live,
            active_boats=active_boats,
            recommended_boats=recommended_boats,
            saturation_ratio=dynamic_saturation,
            predicted_pressure=round(active_boats + recommended_boats * 0.65, 2),
            community_reports=community_reports,
            recommended_species=effective_seed.recommended_species,
            key_reason=(
                regulation.violations[0]
                if regulation is not None and regulation.violations
                else regulation.advisories[0]
                if regulation is not None and regulation.advisories
                else pollution_advisory
                if effective_seed.pollution_risk >= 0.58 and pollution_advisory is not None
                else satellite_advisory
                if (
                    (satellite_productivity_index <= 35 or (turbidity_fnu is not None and turbidity_fnu >= 12))
                    and satellite_advisory is not None
                )
                else weather_advisory
                if marine_condition == "rough" and weather_advisory is not None
                else report_advisory
                if report_advisory is not None
                else f"Zone is under strong pressure with {active_boats} active boats and {recommended_boats} inbound missions."
                if dynamic_saturation >= 1.0
                else f"Zone is becoming crowded with {active_boats} active boats and {recommended_boats} recent recommendations."
                if dynamic_saturation >= 0.6
                else self._reason(effective_seed, overall_score, species)
            ),
        )

    def build_heatmap(
        self,
        departure_port: str,
        species: str,
        profile: FishermanProfilePublic | None = None,
    ) -> HeatmapResponse:
        zone_loads = fleet_service.compute_zone_loads()
        zone_reports = report_service.compute_zone_summaries()
        zone_pollution = {
            seed.id: pollution_service.get_point_assessment(seed.center_lat, seed.center_lon)
            for seed in SEEDED_ZONES
        }
        zone_satellite = {
            seed.id: satellite_service.get_point_observation(seed.center_lat, seed.center_lon)
            for seed in SEEDED_ZONES
        }
        zone_weather = {
            seed.id: weather_service.get_point_forecast(seed.center_lat, seed.center_lon, hours=3)
            for seed in SEEDED_ZONES
        }
        zones = [
            self._score_zone(
                seed,
                departure_port,
                species,
                profile,
                dynamic_saturation=zone_loads[seed.id].pressure_ratio,
                active_boats=zone_loads[seed.id].active_boats,
                recommended_boats=zone_loads[seed.id].recommended_boats,
                report_productivity_signal=zone_reports[seed.id].productivity_signal,
                report_risk_signal=zone_reports[seed.id].risk_signal,
                community_reports=zone_reports[seed.id].total_reports,
                report_advisory=zone_reports[seed.id].advisory,
                pollution_source_name=zone_pollution[seed.id].nearest_source_name,
                pollution_data_live=zone_pollution[seed.id].is_live,
                pollution_index=zone_pollution[seed.id].contamination_index,
                pollution_advisory=zone_pollution[seed.id].advisory,
                dynamic_pollution_risk=zone_pollution[seed.id].risk_score,
                satellite_source=zone_satellite[seed.id].source,
                satellite_live=zone_satellite[seed.id].is_live,
                sst_c=zone_satellite[seed.id].sst_c,
                chlorophyll_mg_m3=zone_satellite[seed.id].chlorophyll_mg_m3,
                salinity_psu=zone_satellite[seed.id].salinity_psu,
                turbidity_fnu=zone_satellite[seed.id].turbidity_fnu,
                satellite_current_speed_kmh=zone_satellite[seed.id].current_speed_kmh,
                satellite_productivity_index=zone_satellite[seed.id].productivity_index,
                satellite_advisory=zone_satellite[seed.id].advisory,
                marine_condition=zone_weather[seed.id].current.condition,
                marine_fishing_score=zone_weather[seed.id].current.fishing_score,
                weather_advisory=zone_weather[seed.id].current.advisory,
                weather_source=zone_weather[seed.id].source,
                weather_live=zone_weather[seed.id].is_live,
            )
            for seed in SEEDED_ZONES
        ]
        zones.sort(key=lambda zone: zone.overall_score, reverse=True)
        return HeatmapResponse(
            departure_port=catalog_service.get_port(departure_port).short_name,
            selected_species=species,
            zones=zones,
            legend=self.legend,
            pollution_plume_origin="Ghannouch chemical corridor",
        )

    def recommend(
        self,
        departure_port: str,
        species: str,
        profile: FishermanProfilePublic | None = None,
    ) -> RecommendationResponse:
        heatmap = self.build_heatmap(departure_port, species, profile)
        eligible = [
            zone
            for zone in heatmap.zones
            if zone.color in {"GREEN", "ORANGE"}
            and zone.overall_score >= self.recommendation_threshold
            and zone.pollution_index < 65
            and zone.marine_condition != "rough"
            and zone.saturation_ratio < 1.15
        ]
        best = eligible[0] if eligible else heatmap.zones[0]
        alternatives = eligible[1:3] if len(eligible) > 1 else heatmap.zones[1:3]
        actionable = len(eligible) > 0
        if actionable:
            advisory = (
                f"{best.label} clears the minimum safe threshold with score {best.overall_score}/100 "
                f"and balanced pressure across active users."
            )
            rationale = [
                f"{best.label} offers the best balance between fish score and legal safety.",
                "The recommendation avoids the Ghannouch plume and protected nursery belt.",
                f"Dynamic fleet load estimates {best.active_boats} active boats and {best.recommended_boats} recent inbound missions in this zone.",
                f"Bathymetric slope is {best.slope_deg} degrees, supporting {species.replace('_', ' ')} habitat fit.",
                f"Surface salinity is {best.salinity_psu if best.salinity_psu is not None else 'n/a'} PSU in this zone.",
                f"Satellite turbidity is {best.turbidity_fnu if best.turbidity_fnu is not None else 'n/a'} FNU in this zone.",
                f"Pollution pressure is {best.pollution_index}/100 with source {best.pollution_source or 'regional background'}.",
                f"Copernicus satellite productivity is {best.satellite_productivity_index}/100 for this zone.",
                f"Marine weather is {best.marine_condition} with a readiness score of {best.marine_fishing_score}/100.",
            ]
        else:
            advisory = (
                "No zone currently clears the minimum safe recommendation threshold. "
                "The system is holding departures instead of sending all users toward weak or risky sectors."
            )
            rationale = [
                "All currently scored zones remain below the minimum safe threshold for an actionable departure.",
                f"Top zone score is {best.overall_score}/100, with pollution {best.pollution_index}/100 and route pressure ratio {best.saturation_ratio}.",
                "The balancing engine prefers to hold departures rather than concentrate multiple boats in low-quality or unsafe areas.",
                "Use the heatmap for monitoring and wait for a better weather, legal, or productivity window.",
            ]
        return RecommendationResponse(
            departure_port=heatmap.departure_port,
            selected_species=species,
            best_zone=best,
            alternatives=alternatives,
            recommendation_status="ACTIONABLE" if actionable else "HOLD",
            minimum_safe_score=self.recommendation_threshold,
            viable_zones_count=len(eligible),
            advisory=advisory,
            rationale=rationale,
        )


zone_engine = ZoneEngine()
