import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from app.core.config import settings


def _database_path() -> Path:
    return Path(settings.sqlite_db_path)


@contextmanager
def get_db_connection() -> Iterator[sqlite3.Connection]:
    db_path = _database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_database() -> None:
    with get_db_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                license_number TEXT,
                license_type TEXT NOT NULL,
                home_port TEXT NOT NULL,
                boat_name TEXT NOT NULL,
                boat_length_m REAL NOT NULL,
                engine_hp INTEGER NOT NULL,
                fuel_capacity_l REAL NOT NULL,
                fuel_consumption_l_per_hour REAL NOT NULL,
                fishing_gears_json TEXT NOT NULL,
                target_species_json TEXT NOT NULL,
                emergency_contacts_json TEXT NOT NULL,
                avatar_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id
            ON user_sessions(user_id);

            CREATE TABLE IF NOT EXISTS fleet_positions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                speed_kmh REAL NOT NULL,
                heading_deg REAL NOT NULL,
                is_at_sea INTEGER NOT NULL,
                note TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_fleet_positions_user_id
            ON fleet_positions(user_id);

            CREATE INDEX IF NOT EXISTS idx_fleet_positions_recorded_at
            ON fleet_positions(recorded_at);

            CREATE TABLE IF NOT EXISTS community_reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                report_type TEXT NOT NULL,
                severity INTEGER NOT NULL,
                species TEXT,
                note TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_community_reports_recorded_at
            ON community_reports(recorded_at);

            CREATE INDEX IF NOT EXISTS idx_community_reports_user_id
            ON community_reports(user_id);

            CREATE TABLE IF NOT EXISTS satellite_observations (
                cache_key TEXT PRIMARY KEY,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                is_live INTEGER NOT NULL,
                observation_timestamp TEXT NOT NULL,
                sst_c REAL,
                chlorophyll_mg_m3 REAL,
                salinity_psu REAL,
                turbidity_fnu REAL,
                suspended_matter_mg_l REAL,
                current_speed_kmh REAL,
                current_direction_deg REAL,
                productivity_index INTEGER NOT NULL,
                turbidity_risk TEXT NOT NULL,
                advisory TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_satellite_observations_created_at
            ON satellite_observations(created_at);

            CREATE TABLE IF NOT EXISTS weather_observations (
                id TEXT PRIMARY KEY,
                cache_key TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                is_live INTEGER NOT NULL,
                current_json TEXT NOT NULL,
                forecast_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_weather_observations_cache_key
            ON weather_observations(cache_key);

            CREATE INDEX IF NOT EXISTS idx_weather_observations_created_at
            ON weather_observations(created_at);

            CREATE TABLE IF NOT EXISTS pollution_sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                base_severity REAL NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pollution_observations (
                id TEXT PRIMARY KEY,
                cache_key TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                source_id TEXT,
                source_name TEXT,
                model_source TEXT NOT NULL,
                status TEXT NOT NULL,
                is_live INTEGER NOT NULL,
                observed_at TEXT NOT NULL,
                risk_score REAL NOT NULL,
                contamination_index INTEGER NOT NULL,
                plume_direction_deg REAL,
                plume_radius_km REAL,
                spread_speed_kmh REAL,
                advisory TEXT NOT NULL,
                FOREIGN KEY(source_id) REFERENCES pollution_sources(id)
            );

            CREATE INDEX IF NOT EXISTS idx_pollution_observations_cache_key
            ON pollution_observations(cache_key);

            CREATE INDEX IF NOT EXISTS idx_pollution_observations_observed_at
            ON pollution_observations(observed_at);

            CREATE TABLE IF NOT EXISTS pollution_plume_history (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                source_name TEXT NOT NULL,
                center_lat REAL NOT NULL,
                center_lon REAL NOT NULL,
                observed_at TEXT NOT NULL,
                plume_direction_deg REAL NOT NULL,
                plume_radius_km REAL NOT NULL,
                spread_speed_kmh REAL NOT NULL,
                core_risk REAL NOT NULL,
                geometry_hint_json TEXT NOT NULL,
                FOREIGN KEY(source_id) REFERENCES pollution_sources(id)
            );

            CREATE INDEX IF NOT EXISTS idx_pollution_plume_history_source
            ON pollution_plume_history(source_id);

            CREATE INDEX IF NOT EXISTS idx_pollution_plume_history_observed_at
            ON pollution_plume_history(observed_at);

            CREATE TABLE IF NOT EXISTS mission_history (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                requested_at TEXT NOT NULL,
                departure_port TEXT NOT NULL,
                selected_species TEXT NOT NULL,
                recommended_zone_id TEXT NOT NULL,
                recommended_zone_label TEXT NOT NULL,
                departure_status TEXT NOT NULL,
                mission_score INTEGER NOT NULL,
                recommendation_json TEXT NOT NULL,
                source_freshness_json TEXT NOT NULL,
                briefing_json TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_mission_history_requested_at
            ON mission_history(requested_at);

            CREATE INDEX IF NOT EXISTS idx_mission_history_user_id
            ON mission_history(user_id);

            CREATE INDEX IF NOT EXISTS idx_mission_history_zone_id
            ON mission_history(recommended_zone_id);

            CREATE TABLE IF NOT EXISTS safety_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                status TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                note TEXT,
                message_preview TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_safety_events_user_id
            ON safety_events(user_id);

            CREATE INDEX IF NOT EXISTS idx_safety_events_created_at
            ON safety_events(created_at);
            """
        )
        for statement in (
            "ALTER TABLE satellite_observations ADD COLUMN salinity_psu REAL",
            "ALTER TABLE satellite_observations ADD COLUMN turbidity_fnu REAL",
            "ALTER TABLE satellite_observations ADD COLUMN suspended_matter_mg_l REAL",
            "ALTER TABLE users ADD COLUMN avatar_url TEXT",
        ):
            try:
                connection.execute(statement)
            except sqlite3.OperationalError:
                pass
        now = datetime.now(UTC).isoformat()
        connection.executemany(
            """
            INSERT INTO pollution_sources (
                id, name, source_type, lat, lon, base_severity, status, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                source_type = excluded.source_type,
                lat = excluded.lat,
                lon = excluded.lon,
                base_severity = excluded.base_severity,
                status = excluded.status,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            [
                (
                    "ghannouch_phosphate",
                    "Ghannouch industrial corridor",
                    "industrial_outfall",
                    33.952,
                    10.120,
                    0.92,
                    "active",
                    "Primary modeled contamination source impacting the inner Gulf of Gabes.",
                    now,
                    now,
                ),
                (
                    "teboulbou_urban",
                    "Teboulbou urban discharge",
                    "urban_outfall",
                    33.886,
                    10.115,
                    0.54,
                    "active",
                    "Secondary coastal urban effluent source with moderate local spread.",
                    now,
                    now,
                ),
                (
                    "akarit_runoff",
                    "Oued Akarit runoff mouth",
                    "seasonal_runoff",
                    34.015,
                    10.022,
                    0.47,
                    "seasonal",
                    "Seasonal runoff source that can intensify after rain events.",
                    now,
                    now,
                ),
            ],
        )
