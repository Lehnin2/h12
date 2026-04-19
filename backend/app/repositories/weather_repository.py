from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.db.database import get_db_connection
from app.models.weather import MarineWeatherResponse, MarineWeatherSnapshot


def _cache_key(lat: float, lon: float, hours: int) -> str:
    return f"{round(lat, 3):.3f}:{round(lon, 3):.3f}:{hours}"


class WeatherRepository:
    def get_recent_forecast(
        self,
        lat: float,
        lon: float,
        hours: int,
        max_age: timedelta,
    ) -> MarineWeatherResponse | None:
        cutoff = (datetime.now(UTC) - max_age).isoformat()
        with get_db_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM weather_observations
                WHERE cache_key = ?
                  AND created_at >= ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (_cache_key(lat, lon, hours), cutoff),
            ).fetchone()
            if row is None:
                return None

        current = MarineWeatherSnapshot(**json.loads(row["current_json"]))
        forecast = [MarineWeatherSnapshot(**item) for item in json.loads(row["forecast_json"])]
        return MarineWeatherResponse(
            lat=row["lat"],
            lon=row["lon"],
            source=row["source"],
            status=row["status"],
            is_live=bool(row["is_live"]),
            current=current,
            forecast=forecast,
        )

    def store_forecast(self, payload: MarineWeatherResponse, hours: int) -> None:
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO weather_observations (
                    id, cache_key, lat, lon, source, status, is_live, current_json, forecast_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    _cache_key(payload.lat, payload.lon, hours),
                    payload.lat,
                    payload.lon,
                    payload.source,
                    payload.status,
                    1 if payload.is_live else 0,
                    json.dumps(payload.current.model_dump()),
                    json.dumps([item.model_dump() for item in payload.forecast]),
                    datetime.now(UTC).isoformat(),
                ),
            )


weather_repository = WeatherRepository()

