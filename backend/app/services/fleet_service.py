from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from app.domain.zone_seed import SEEDED_ZONES
from app.models.fleet import (
    FleetOverviewResponse,
    FleetPositionCreate,
    FleetPositionSnapshot,
    ZoneLoadSnapshot,
)
from app.repositories.fleet_repository import fleet_repository
from app.repositories.mission_repository import mission_repository
from app.services.utils import haversine_km


ZONE_CAPACITIES: dict[str, int] = {
    "gabes_north_red": 2,
    "zarrat_c3": 6,
    "zarrat_south_green": 5,
    "mareth_orange": 4,
    "protected_black": 1,
    "akarit_green": 6,
}


class FleetService:
    def register_position(self, user_id: str, payload: FleetPositionCreate) -> None:
        fleet_repository.create_position(user_id, payload)

    def _nearest_zone(self, lat: float, lon: float) -> tuple[str | None, str | None]:
        best_zone = None
        best_distance = None
        for zone in SEEDED_ZONES:
            distance = haversine_km(lat, lon, zone.center_lat, zone.center_lon)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_zone = zone
        if best_zone is None:
            return None, None
        if best_distance is not None and best_distance > 18:
            return None, None
        return best_zone.id, best_zone.label

    def list_active_positions(self, within_minutes: int = 240) -> list[FleetPositionSnapshot]:
        positions = fleet_repository.list_active_positions(within_minutes)
        enriched: list[FleetPositionSnapshot] = []
        for position in positions:
            zone_id, zone_label = self._nearest_zone(position.lat, position.lon)
            enriched.append(
                position.model_copy(
                    update={
                        "assigned_zone_id": zone_id,
                        "assigned_zone_label": zone_label,
                    }
                )
            )
        return [item for item in enriched if item.is_at_sea]

    def compute_zone_loads(self, within_minutes: int = 240) -> dict[str, ZoneLoadSnapshot]:
        positions = self.list_active_positions(within_minutes)
        recent_recommendations = mission_repository.count_recent_zone_recommendations(within_minutes=120)
        counts = Counter(
            position.assigned_zone_id for position in positions if position.assigned_zone_id is not None
        )
        snapshots: dict[str, ZoneLoadSnapshot] = {}
        for zone in SEEDED_ZONES:
            capacity = ZONE_CAPACITIES.get(zone.id, 4)
            active_boats = counts.get(zone.id, 0)
            saturation = round(min(active_boats / capacity, 1.5), 2)
            recommended_boats = recent_recommendations.get(zone.id, 0)
            predicted_pressure = round(active_boats + recommended_boats * 0.65, 2)
            pressure_ratio = round(min(predicted_pressure / capacity, 1.8), 2)
            snapshots[zone.id] = ZoneLoadSnapshot(
                zone_id=zone.id,
                zone_label=zone.label,
                active_boats=active_boats,
                recommended_boats=recommended_boats,
                capacity=capacity,
                saturation_ratio=saturation,
                predicted_pressure=predicted_pressure,
                pressure_ratio=pressure_ratio,
            )
        return snapshots

    def overview(self, within_minutes: int = 240) -> FleetOverviewResponse:
        positions = self.list_active_positions(within_minutes)
        loads = self.compute_zone_loads(within_minutes)
        return FleetOverviewResponse(
            active_boats=len(positions),
            active_positions=positions,
            zone_loads=list(loads.values()),
        )

    def latest_sync_timestamp(self, within_minutes: int = 240) -> str | None:
        return fleet_repository.latest_position_timestamp(within_minutes)

    def freshness_snapshot(self, within_minutes: int = 240) -> tuple[str | None, bool]:
        latest_timestamp = self.latest_sync_timestamp(within_minutes)
        if latest_timestamp is None:
            return None, False
        latest = datetime.fromisoformat(latest_timestamp)
        age_minutes = (datetime.now(UTC) - latest).total_seconds() / 60
        return latest_timestamp, age_minutes <= within_minutes


fleet_service = FleetService()
