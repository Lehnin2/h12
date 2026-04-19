from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import sin

import requests

from app.core.config import settings
from app.models.weather import MarineWeatherResponse, MarineWeatherSnapshot
from app.repositories.weather_repository import weather_repository
from app.services.catalog_service import catalog_service


class WeatherService:
    endpoint = "https://api.stormglass.io/v2/weather/point"
    requested_params = [
        "airTemperature",
        "waterTemperature",
        "windSpeed",
        "windDirection",
        "waveHeight",
        "currentSpeed",
        "gust",
        "precipitation",
    ]
    preferred_sources = [
        "noaa",
        "sg",
        "icon",
        "dwd",
        "meto",
        "fcoo",
    ]
    cache_ttl = timedelta(minutes=20)

    def __init__(self) -> None:
        self._response_cache: dict[tuple[float, float, int], tuple[datetime, MarineWeatherResponse]] = {}

    def _meters_per_second_to_kmh(self, value: float | None) -> float | None:
        if value is None:
            return None
        return round(value * 3.6, 1)

    def _pick_provider_value(self, raw: object) -> float | None:
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, dict):
            for provider in self.preferred_sources:
                value = raw.get(provider)
                if isinstance(value, (int, float)):
                    return float(value)
            for value in raw.values():
                if isinstance(value, (int, float)):
                    return float(value)
        return None

    def _condition_label(
        self,
        wind_speed_kmh: float | None,
        wave_height_m: float | None,
        precipitation_mm_per_hour: float | None,
    ) -> str:
        wind = wind_speed_kmh or 0.0
        wave = wave_height_m or 0.0
        rain = precipitation_mm_per_hour or 0.0
        if wave >= 2.2 or wind >= 36 or rain >= 4:
            return "rough"
        if wave >= 1.4 or wind >= 24 or rain >= 1.5:
            return "moderate"
        return "calm"

    def _advisory(self, condition: str, wind_speed_kmh: float | None, wave_height_m: float | None) -> str:
        wind = wind_speed_kmh or 0.0
        wave = wave_height_m or 0.0
        if condition == "rough":
            return "Unsafe departure window for small artisanal boats. Reassess route and delay departure."
        if condition == "moderate":
            if wind >= 28:
                return "Manageable but fuel consumption and drift risk are rising. Favor nearby legal zones."
            if wave >= 1.5:
                return "Sea state is moderate. Keep shorter loops and avoid exposed sectors."
            return "Moderate marine conditions. Navigate carefully and keep conservative timing."
        return "Good marine window for departure with stable wind and manageable sea state."

    def _fishing_score(
        self,
        wind_speed_kmh: float | None,
        wave_height_m: float | None,
        current_speed_kmh: float | None,
    ) -> int:
        wind_penalty = min((wind_speed_kmh or 0.0) * 1.1, 40)
        wave_penalty = min((wave_height_m or 0.0) * 18, 35)
        current_penalty = min((current_speed_kmh or 0.0) * 1.3, 20)
        return max(5, min(95, round(86 - wind_penalty - wave_penalty - current_penalty)))

    def _build_snapshot(self, timestamp: str, hour_data: dict[str, object]) -> MarineWeatherSnapshot:
        wind_speed_kmh = self._meters_per_second_to_kmh(
            self._pick_provider_value(hour_data.get("windSpeed"))
        )
        current_speed_kmh = self._meters_per_second_to_kmh(
            self._pick_provider_value(hour_data.get("currentSpeed"))
        )
        gust_kmh = self._meters_per_second_to_kmh(self._pick_provider_value(hour_data.get("gust")))
        wave_height_m = self._pick_provider_value(hour_data.get("waveHeight"))
        precipitation = self._pick_provider_value(hour_data.get("precipitation"))
        condition = self._condition_label(wind_speed_kmh, wave_height_m, precipitation)

        return MarineWeatherSnapshot(
            timestamp=timestamp,
            air_temperature_c=self._pick_provider_value(hour_data.get("airTemperature")),
            water_temperature_c=self._pick_provider_value(hour_data.get("waterTemperature")),
            wind_speed_kmh=wind_speed_kmh,
            wind_direction_deg=self._pick_provider_value(hour_data.get("windDirection")),
            wave_height_m=wave_height_m,
            current_speed_kmh=current_speed_kmh,
            gust_kmh=gust_kmh,
            precipitation_mm_per_hour=precipitation,
            condition=condition,
            fishing_score=self._fishing_score(wind_speed_kmh, wave_height_m, current_speed_kmh),
            advisory=self._advisory(condition, wind_speed_kmh, wave_height_m),
        )

    def _fallback_forecast(self, lat: float, lon: float, hours: int) -> MarineWeatherResponse:
        now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        sea_bias = abs(sin(lat * 0.7) + sin(lon * 0.4))
        forecast: list[MarineWeatherSnapshot] = []
        for offset in range(max(hours, 1)):
            timestamp = (now + timedelta(hours=offset)).isoformat()
            wind_speed_kmh = round(11 + sea_bias * 7 + (offset % 4) * 1.8, 1)
            wave_height_m = round(0.4 + sea_bias * 0.6 + (offset % 3) * 0.12, 1)
            current_speed_kmh = round(1.7 + sea_bias * 1.3 + (offset % 2) * 0.35, 1)
            condition = self._condition_label(wind_speed_kmh, wave_height_m, 0.0)
            forecast.append(
                MarineWeatherSnapshot(
                    timestamp=timestamp,
                    air_temperature_c=round(19 + sea_bias * 6 + (offset % 5) * 0.7, 1),
                    water_temperature_c=round(17 + sea_bias * 4 + (offset % 4) * 0.4, 1),
                    wind_speed_kmh=wind_speed_kmh,
                    wind_direction_deg=round((145 + offset * 18) % 360, 0),
                    wave_height_m=wave_height_m,
                    current_speed_kmh=current_speed_kmh,
                    gust_kmh=round(wind_speed_kmh * 1.25, 1),
                    precipitation_mm_per_hour=0.0,
                    condition=condition,
                    fishing_score=self._fishing_score(wind_speed_kmh, wave_height_m, current_speed_kmh),
                    advisory=self._advisory(condition, wind_speed_kmh, wave_height_m),
                )
            )

        return MarineWeatherResponse(
            lat=lat,
            lon=lon,
            source="seeded_fallback",
            status="success",
            is_live=False,
            current=forecast[0],
            forecast=forecast,
        )

    def get_point_forecast(self, lat: float, lon: float, hours: int = 8) -> MarineWeatherResponse:
        cache_key = (round(lat, 3), round(lon, 3), hours)
        now = datetime.now(UTC)
        cached = self._response_cache.get(cache_key)
        if cached is not None:
            cached_at, cached_response = cached
            if now - cached_at <= self.cache_ttl:
                return cached_response
        persisted = weather_repository.get_recent_forecast(lat, lon, hours, self.cache_ttl)
        if persisted is not None:
            self._response_cache[cache_key] = (now, persisted)
            return persisted

        if not settings.stormglass_api_key:
            fallback = self._fallback_forecast(lat, lon, hours)
            self._response_cache[cache_key] = (now, fallback)
            weather_repository.store_forecast(fallback, hours)
            return fallback

        try:
            response = requests.get(
                self.endpoint,
                params={
                    "lat": lat,
                    "lng": lon,
                    "params": ",".join(self.requested_params),
                },
                headers={"Authorization": settings.stormglass_api_key},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            raw_hours = payload.get("hours", [])
            if not raw_hours:
                fallback = self._fallback_forecast(lat, lon, hours)
                self._response_cache[cache_key] = (now, fallback)
                weather_repository.store_forecast(fallback, hours)
                return fallback

            forecast = [
                self._build_snapshot(item.get("time", datetime.now(UTC).isoformat()), item)
                for item in raw_hours[: max(hours, 1)]
            ]
            live_response = MarineWeatherResponse(
                lat=lat,
                lon=lon,
                source="stormglass",
                status="success",
                is_live=True,
                current=forecast[0],
                forecast=forecast,
            )
            self._response_cache[cache_key] = (now, live_response)
            weather_repository.store_forecast(live_response, hours)
            return live_response
        except requests.RequestException:
            fallback = self._fallback_forecast(lat, lon, hours)
            self._response_cache[cache_key] = (now, fallback)
            weather_repository.store_forecast(fallback, hours)
            return fallback

    def get_port_forecast(self, port_id: str, hours: int = 8) -> MarineWeatherResponse:
        port = catalog_service.get_port(port_id)
        return self.get_point_forecast(port.lat, port.lon, hours)


weather_service = WeatherService()
