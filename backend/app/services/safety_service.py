from app.models.fleet import FleetPositionCreate
from app.models.profile import FishermanProfilePublic
from app.models.regulation import RegulationAssessmentResponse
from app.models.routing import RouteResponse
from app.models.safety import (
    SafetyCheckInCreate,
    SafetyEventListResponse,
    SafetyEventResponse,
    SafetySosCreate,
    SafetyStatusResponse,
)
from app.services.catalog_service import catalog_service
from app.repositories.safety_repository import safety_repository
from app.services.fleet_service import fleet_service
from app.services.notification_service import notification_service
from app.services.vapi_service import trigger_vapi_sos_call
from app.models.weather import MarineWeatherResponse
from app.core.config import settings


class SafetyService:
    def _message_preview(
        self,
        profile: FishermanProfilePublic | None,
        port_short_name: str,
        lat: float,
        lon: float,
        mode: str,
        note: str | None = None,
    ) -> str:
        label = profile.boat_name if profile is not None else "mission-unit"
        note_chunk = f" NOTE:{note}" if note else ""
        return (
            f"URGENCE PECHEUR PORT:{port_short_name} GPS:{lat:.3f},{lon:.3f} "
            f"BOAT:{label} MODE:{mode} CONTACT:HARAS_WATANI{note_chunk}"
        )

    def _safety_sms_body(
        self,
        profile: FishermanProfilePublic,
        event_type: str,
        lat: float,
        lon: float,
        note: str | None,
    ) -> str:
        port_short_name = catalog_service.get_port(profile.home_port).short_name
        note_chunk = f" Note: {note}." if note else ""
        return (
            f"Guardian of the Gulf {event_type}: boat {profile.boat_name}, "
            f"captain {profile.full_name}, port {port_short_name}, "
            f"GPS {lat:.5f},{lon:.5f}.{note_chunk}"
        )

    def get_status(
        self,
        departure_port: str,
        weather: MarineWeatherResponse | None = None,
        route: RouteResponse | None = None,
        regulation: RegulationAssessmentResponse | None = None,
        profile: FishermanProfilePublic | None = None,
    ) -> SafetyStatusResponse:
        port = catalog_service.get_port(departure_port)
        preview = self._message_preview(profile, port.short_name, port.lat, port.lon, "OFFLINE")
        blocking_reasons: list[str] = []
        recommended_checks = [
            "Confirm phone battery and offline GPS cache before departure.",
            "Send departure check-in to the safety contact list.",
            "Verify fuel margin against the planned route and return leg.",
        ]
        departure_status = "GO"
        safety_score = 86

        if weather is not None:
            if weather.current.condition == "rough":
                departure_status = "NO_GO"
                safety_score -= 38
                blocking_reasons.append(weather.current.advisory)
            elif weather.current.condition == "moderate":
                departure_status = "CAUTION"
                safety_score -= 16
                recommended_checks.append("Delay departure if wave band strengthens in the next hour.")

        if route is not None:
            if route.route_risk_level == "HIGH":
                departure_status = "NO_GO" if departure_status == "GO" else departure_status
                safety_score -= 24
                blocking_reasons.append("Route crosses shallow or unsafe bathymetry for a routine departure.")
            elif route.route_risk_level == "MEDIUM" and departure_status == "GO":
                departure_status = "CAUTION"
                safety_score -= 10

        if regulation is not None:
            if regulation.overall_status == "PROHIBITED":
                departure_status = "NO_GO"
                safety_score = min(safety_score, 18)
                blocking_reasons.extend(regulation.violations[:2])
            elif regulation.overall_status == "RESTRICTED" and departure_status == "GO":
                departure_status = "CAUTION"
                safety_score -= 8
                recommended_checks.append("Respect restricted gear or species rules before leaving port.")

        if departure_status == "GO":
            recommended_action = "Departure window is acceptable. Keep SOS enabled and confirm departure check-in."
        elif departure_status == "CAUTION":
            recommended_action = "Departure is possible with caution. Reduce range, shorten loops, and monitor conditions."
        else:
            recommended_action = "Do not depart now. Wait for a safer window or switch to a safer nearby mission."

        last_check_in_at = None
        open_incidents = 0
        emergency_contacts = [
            "Haras Watani",
            "Capitainerie locale",
            "Contact famille principal",
        ]
        if profile is not None:
            last_check_in = safety_repository.latest_check_in(profile.id)
            last_check_in_at = last_check_in.created_at if last_check_in is not None else None
            open_incidents = safety_repository.open_incidents_count(profile.id)
            emergency_contacts = [
                f"{contact.name} ({contact.relation})"
                for contact in profile.emergency_contacts
            ] or emergency_contacts

        return SafetyStatusResponse(
            departure_port=port.short_name,
            departure_status=departure_status,
            safety_score=max(5, min(100, safety_score)),
            gps_status="Offline-capable local GPS trail ready",
            last_sync_mode="Cached marine layers + SMS fallback",
            emergency_contacts=emergency_contacts,
            emergency_message_preview=preview,
            blocking_reasons=blocking_reasons,
            recommended_checks=recommended_checks,
            recommended_action=recommended_action,
            last_check_in_at=last_check_in_at,
            open_incidents=open_incidents,
        )

    def create_check_in(
        self,
        profile: FishermanProfilePublic,
        payload: SafetyCheckInCreate,
    ) -> SafetyEventResponse:
        fleet_service.register_position(
            profile.id,
            FleetPositionCreate(
                lat=payload.lat,
                lon=payload.lon,
                speed_kmh=0.0,
                heading_deg=0.0,
                is_at_sea=True,
                note=f"check-in {payload.note}" if payload.note else "check-in",
            ),
        )
        message_preview = self._message_preview(
            profile,
            catalog_service.get_port(profile.home_port).short_name,
            payload.lat,
            payload.lon,
            payload.sync_mode.upper(),
            payload.note,
        )
        sms_results = notification_service.send_safety_broadcast(
            profile.emergency_contacts,
            self._safety_sms_body(profile, "CHECK-IN", payload.lat, payload.lon, payload.note),
        )
        return safety_repository.create_event(
            user_id=profile.id,
            event_type="CHECK_IN",
            status="RECORDED",
            lat=payload.lat,
            lon=payload.lon,
            note=payload.note,
            message_preview=message_preview,
            payload={
                "battery_level_pct": payload.battery_level_pct,
                "sync_mode": payload.sync_mode,
                "boat_name": profile.boat_name,
                "sms_results": sms_results,
            },
        )

    def trigger_sos(
        self,
        profile: FishermanProfilePublic,
        payload: SafetySosCreate,
    ) -> SafetyEventResponse:
        fleet_service.register_position(
            profile.id,
            FleetPositionCreate(
                lat=payload.lat,
                lon=payload.lon,
                speed_kmh=0.0,
                heading_deg=0.0,
                is_at_sea=True,
                note=f"sos {payload.message}" if payload.message else "sos",
            ),
        )
        message_preview = self._message_preview(
            profile,
            catalog_service.get_port(profile.home_port).short_name,
            payload.lat,
            payload.lon,
            "SOS",
            payload.message,
        )
        sms_results = notification_service.send_safety_broadcast(
            profile.emergency_contacts,
            self._safety_sms_body(profile, "SOS", payload.lat, payload.lon, payload.message),
        )
        
        vapi_called = False
        if settings.vapi_emergency_number:
            friendly_message = f"Emergency SOS from boat {profile.boat_name}."
            if payload.message:
                friendly_message += f" Note: {payload.message}"
                
            vapi_called = trigger_vapi_sos_call(
                boat_name=profile.boat_name,
                lat=payload.lat,
                lon=payload.lon,
                message=friendly_message,
                phone_number=settings.vapi_emergency_number
            )

        return safety_repository.create_event(
            user_id=profile.id,
            event_type="SOS",
            status="OPEN",
            lat=payload.lat,
            lon=payload.lon,
            note=payload.message,
            message_preview=message_preview,
            payload={
                "boat_name": profile.boat_name,
                "contacts": [contact.model_dump() for contact in profile.emergency_contacts],
                "sms_results": sms_results,
                "vapi_sent": vapi_called,
            },
        )

    def list_events(self, user_id: str, limit: int = 20) -> SafetyEventListResponse:
        return SafetyEventListResponse(events=safety_repository.list_recent_events(user_id, limit))


safety_service = SafetyService()
