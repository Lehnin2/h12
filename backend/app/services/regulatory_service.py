from __future__ import annotations

from datetime import UTC, date, datetime
from functools import lru_cache
from pathlib import Path

from PIL import Image

from app.domain.regulation_rules import (
    GEAR_BANS,
    LICENSE_ALLOWED_GEARS,
    PROTECTED_AREAS,
    SPECIES_SEASONS,
    ZONE_MAP_RULES,
)
from app.models.profile import FishermanProfilePublic
from app.models.regulation import ProtectedAreaMatch, RegulationAssessmentResponse
from app.services.utils import haversine_km


class RegulatoryService:
    def __init__(self) -> None:
        self.maps_dir = Path(__file__).resolve().parents[2] / "data" / "regulation_maps"

    @lru_cache(maxsize=8)
    def _load_image(self, image_name: str) -> Image.Image:
        return Image.open(self.maps_dir / image_name).convert("RGB")

    def _map_point(self, lat: float, lon: float, width: int, height: int) -> tuple[int, int]:
        x = int((lon - 7.5) / (12.5 - 7.5) * width)
        y = int((38.5 - lat) / (38.5 - 33.5) * height)
        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))
        return x, y

    def _pixel_matches(self, pixel: tuple[int, int, int], target: tuple[int, int, int], tolerance: int) -> bool:
        return all(abs(channel - ref) <= tolerance for channel, ref in zip(pixel, target, strict=True))

    def _month_day_in_range(self, current: str, start: str, end: str) -> bool:
        if start <= end:
            return start <= current <= end
        return current >= start or current <= end

    def _parse_date_key(self, current_date: str | None) -> str:
        if current_date:
            value = date.fromisoformat(current_date)
        else:
            value = datetime.now(UTC).date()
        return value.strftime("%d-%m")

    def _zone_label(self, lat: float, lon: float) -> str:
        image = self._load_image("carte_trois_bleu_tunisie.PNG")
        x, y = self._map_point(lat, lon, image.width, image.height)
        pixel = image.getpixel((x, y))
        if self._pixel_matches(pixel, (0, 0, 255), 55):
            return "North Zone"
        if self._pixel_matches(pixel, (0, 255, 0), 55):
            return "Center Zone"
        if self._pixel_matches(pixel, (255, 0, 0), 55):
            return "South Zone"
        if self._pixel_matches(pixel, (255, 255, 255), 55):
            return "Land"
        return "Unknown Zone"

    def _protected_area_matches(self, lat: float, lon: float) -> list[ProtectedAreaMatch]:
        matches: list[ProtectedAreaMatch] = []
        for area in PROTECTED_AREAS:
            distance = haversine_km(lat, lon, float(area["lat"]), float(area["lon"]))
            if distance <= 15:
                matches.append(
                    ProtectedAreaMatch(
                        name=str(area["name"]),
                        status=str(area["status"]),
                        distance_km=round(distance, 2),
                        proximity="inside" if distance <= 1 else "near",
                    )
                )
        matches.sort(key=lambda item: item.distance_km)
        return matches

    def _apply_image_rules(
        self,
        lat: float,
        lon: float,
        gear: str | None,
        violations: list[str],
        advisories: list[str],
        references: list[str],
    ) -> None:
        normalized_gear = (gear or "").lower()
        for rule in ZONE_MAP_RULES:
            image = self._load_image(str(rule["image_name"]))
            x, y = self._map_point(lat, lon, image.width, image.height)
            pixel = image.getpixel((x, y))
            if self._pixel_matches(pixel, rule["target_rgb"], int(rule["tolerance"])):
                applies_to = {item.lower() for item in rule["applies_to_gears"]}
                if applies_to and normalized_gear not in applies_to:
                    advisories.append(str(rule["message"]))
                elif str(rule["effect"]) == "PROHIBITED":
                    violations.append(str(rule["message"]))
                else:
                    advisories.append(str(rule["message"]))
                references.append(f"Map rule: {rule['id']}")

    def _apply_license_rules(
        self,
        gear: str | None,
        license_type: str | None,
        violations: list[str],
        references: list[str],
    ) -> None:
        if not gear or not license_type:
            return
        allowed = LICENSE_ALLOWED_GEARS.get(license_type.lower())
        if allowed is None:
            return
        if gear.lower() not in {item.lower() for item in allowed}:
            violations.append(f"Gear '{gear}' is not allowed for license type '{license_type}'.")
            references.append("Guardian profile policy: gear by license type")

    def _apply_gear_rules(
        self,
        gear: str | None,
        species: str | None,
        violations: list[str],
        advisories: list[str],
        references: list[str],
    ) -> None:
        if not gear:
            return
        normalized = gear.lower()
        for banned_gear, reason in GEAR_BANS.items():
            if banned_gear.lower() == normalized:
                violations.append(reason)
                references.append("Loi 75-17: prohibited gear/method")
                return
        if normalized == "feu" and species and species.lower() in {"sardine", "anchois"}:
            advisories.append("Fire fishing has legal exceptions only in narrow migratory cases; verify local authorization.")
            references.append("Loi 75-17: fire fishing with exceptions")

    def _apply_species_rules(
        self,
        species: str | None,
        gear: str | None,
        current_key: str,
        violations: list[str],
        advisories: list[str],
        references: list[str],
    ) -> None:
        if not species:
            return
        normalized = species.lower()
        rule = SPECIES_SEASONS.get(normalized)
        if not rule:
            return
        windows = rule["windows"]
        in_window = any(self._month_day_in_range(current_key, start, end) for start, end in windows)
        mode = rule["mode"]
        if mode == "allowed_only" and not in_window:
            violations.append(f"Species '{species}' is outside its permitted fishing season.")
        elif mode == "prohibited" and in_window:
            violations.append(f"Species '{species}' is in a closed season.")
        required_gear = rule.get("required_gear")
        if required_gear and gear and gear.lower() != str(required_gear).lower():
            advisories.append(f"Species '{species}' is usually regulated with gear '{required_gear}'.")
        references.append(str(rule["reference"]))

    def assess(
        self,
        lat: float,
        lon: float,
        species: str | None = None,
        gear: str | None = None,
        license_type: str | None = None,
        current_date: str | None = None,
    ) -> RegulationAssessmentResponse:
        violations: list[str] = []
        advisories: list[str] = []
        references: list[str] = []
        date_key = self._parse_date_key(current_date)
        protected_areas = self._protected_area_matches(lat, lon)
        fishing_zone = self._zone_label(lat, lon)

        for match in protected_areas:
            if match.proximity == "inside":
                violations.append(f"Inside protected area: {match.name}.")
            else:
                advisories.append(f"Near protected area: {match.name} ({match.distance_km} km).")
            references.append(match.status)

        if fishing_zone == "Land":
            violations.append("The selected point falls on land, not in an operational fishing zone.")

        self._apply_image_rules(lat, lon, gear, violations, advisories, references)
        self._apply_license_rules(gear, license_type, violations, references)
        self._apply_gear_rules(gear, species, violations, advisories, references)
        self._apply_species_rules(species, gear, date_key, violations, advisories, references)

        overall_status = "OPEN"
        if violations:
            overall_status = "PROHIBITED"
        elif advisories:
            overall_status = "RESTRICTED"

        deduped_refs = list(dict.fromkeys(references))
        deduped_advisories = list(dict.fromkeys(advisories))
        deduped_violations = list(dict.fromkeys(violations))

        return RegulationAssessmentResponse(
            lat=lat,
            lon=lon,
            species=species,
            gear=gear,
            license_type=license_type,
            date=current_date or datetime.now(UTC).date().isoformat(),
            fishing_zone=fishing_zone,
            overall_status=overall_status,
            protected_areas=protected_areas,
            violations=deduped_violations,
            advisories=deduped_advisories,
            references=deduped_refs,
        )

    def assess_for_profile(
        self,
        lat: float,
        lon: float,
        profile: FishermanProfilePublic,
        species: str | None = None,
        current_date: str | None = None,
    ) -> RegulationAssessmentResponse:
        primary_species = species or (profile.target_species[0] if profile.target_species else None)
        primary_gear = profile.fishing_gears[0] if profile.fishing_gears else None
        return self.assess(
            lat=lat,
            lon=lon,
            species=primary_species,
            gear=primary_gear,
            license_type=profile.license_type,
            current_date=current_date,
        )


regulatory_service = RegulatoryService()

