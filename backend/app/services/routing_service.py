from app.domain.zone_seed import SEEDED_ZONES
from app.models.profile import FishermanProfilePublic
from app.models.routing import RouteLeg, RouteResponse
from app.models.shared import GeoPoint
from app.services.bathymetry_service import bathymetry_service
from app.services.catalog_service import catalog_service
from app.services.utils import haversine_km
from app.services.weather_service import weather_service


class RoutingService:
    def optimize(
        self,
        departure_port: str,
        target_zone_id: str,
        profile: FishermanProfilePublic | None = None,
    ) -> RouteResponse:
        port = catalog_service.get_port(departure_port)
        zone = next((item for item in SEEDED_ZONES if item.id == target_zone_id), SEEDED_ZONES[0])

        direct_distance = haversine_km(port.lat, port.lon, zone.center_lat, zone.center_lon)
        corridor_point = GeoPoint(
            lat=(port.lat + zone.center_lat) / 2 + 0.03,
            lon=(port.lon + zone.center_lon) / 2 - 0.05,
        )

        target_weather = weather_service.get_point_forecast(zone.center_lat, zone.center_lon, hours=3)
        corridor_weather = weather_service.get_point_forecast(corridor_point.lat, corridor_point.lon, hours=3)
        dominant_weather = (
            target_weather.current
            if target_weather.current.fishing_score <= corridor_weather.current.fishing_score
            else corridor_weather.current
        )

        optimized_distance = direct_distance * 1.11
        boat_speed = 18.5
        fuel_rate = 0.58
        if profile is not None:
            boat_speed = max(12.0, min(26.0, 10 + profile.engine_hp / 7.5))
            fuel_rate = max(0.42, profile.fuel_consumption_l_per_hour / boat_speed)
        if dominant_weather.condition == "rough":
            boat_speed *= 0.74
            optimized_distance *= 1.08
        elif dominant_weather.condition == "moderate":
            boat_speed *= 0.88
            optimized_distance *= 1.03
        estimated_duration_h = round(optimized_distance / boat_speed, 2)
        estimated_fuel_l = round(optimized_distance * fuel_rate, 1)
        direct_fuel_l = round(direct_distance * 0.73, 1)
        depth_samples = bathymetry_service.sample_depths_along_line(
            port.lat,
            port.lon,
            zone.center_lat,
            zone.center_lon,
            samples=7,
        )
        min_depth = round(min(depth_samples), 1)
        max_depth = round(max(depth_samples), 1)
        route_risk_level = "LOW"
        if min_depth < 8:
            route_risk_level = "HIGH"
        elif min_depth < 12:
            route_risk_level = "MEDIUM"

        weather_risk_level = "LOW"
        route_readiness = "GO"
        if dominant_weather.condition == "rough":
            weather_risk_level = "HIGH"
            route_risk_level = "HIGH"
            route_readiness = "NO_GO"
        elif dominant_weather.condition == "moderate":
            weather_risk_level = "MEDIUM"
            if route_risk_level != "HIGH":
                route_risk_level = "MEDIUM"
            route_readiness = "CAUTION"
        elif route_risk_level == "HIGH":
            route_readiness = "CAUTION"

        notes = [
            "Route bends away from the Ghannouch plume corridor.",
            "Protected nursery belt is excluded from the optimized path.",
            f"Sea state on the route is {dominant_weather.condition} with wind around "
            f"{dominant_weather.wind_speed_kmh or 0:.1f} km/h.",
        ]
        if min_depth < 8:
            notes.append("Shallow bathymetry detected along part of the lane, proceed with caution.")
        else:
            notes.append(f"Sampled bathymetry stays between {min_depth}m and {max_depth}m on this route.")
        if dominant_weather.condition == "rough":
            notes.append("Wave and wind conditions make this lane unsafe for a standard artisanal departure.")
        elif dominant_weather.condition == "moderate":
            notes.append("Weather remains manageable, but route timing and fuel margin should stay conservative.")

        return RouteResponse(
            departure_port=port.short_name,
            target_zone_id=zone.id,
            direct_distance_km=round(direct_distance, 1),
            optimized_distance_km=round(optimized_distance, 1),
            estimated_duration_h=estimated_duration_h,
            estimated_fuel_l=estimated_fuel_l,
            savings_l=round(max(direct_fuel_l - estimated_fuel_l, 0.8), 1),
            min_depth_m=min_depth,
            max_depth_m=max_depth,
            route_risk_level=route_risk_level,
            weather_risk_level=weather_risk_level,
            route_readiness=route_readiness,
            sea_state_summary=dominant_weather.advisory,
            path=[
                RouteLeg(
                    label=f"{port.short_name} departure",
                    point=GeoPoint(lat=port.lat, lon=port.lon),
                    safety_state="SAFE",
                ),
                RouteLeg(
                    label="Safe corridor pivot",
                    point=corridor_point,
                    safety_state="CAUTION",
                ),
                RouteLeg(
                    label=zone.label,
                    point=GeoPoint(lat=zone.center_lat, lon=zone.center_lon),
                    safety_state="TARGET",
                ),
            ],
            safety_notes=notes,
        )


routing_service = RoutingService()
