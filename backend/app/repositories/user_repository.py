import json
from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import is_admin_email
from app.db.database import get_db_connection
from app.models.profile import (
    EmergencyContact,
    FishermanProfileCreate,
    FishermanProfilePublic,
    FishermanProfileUpdate,
)


def _serialize_contacts(contacts: list[EmergencyContact]) -> str:
    return json.dumps([contact.model_dump() for contact in contacts])


def _serialize_list(values: list[str]) -> str:
    return json.dumps(values)


def _row_to_profile(row) -> FishermanProfilePublic:
    return FishermanProfilePublic(
        id=row["id"],
        email=row["email"],
        is_admin=is_admin_email(row["email"]),
        full_name=row["full_name"],
        license_number=row["license_number"],
        license_type=row["license_type"],
        home_port=row["home_port"],
        boat_name=row["boat_name"],
        boat_length_m=row["boat_length_m"],
        engine_hp=row["engine_hp"],
        fuel_capacity_l=row["fuel_capacity_l"],
        fuel_consumption_l_per_hour=row["fuel_consumption_l_per_hour"],
        fishing_gears=json.loads(row["fishing_gears_json"]),
        target_species=json.loads(row["target_species_json"]),
        emergency_contacts=[
            EmergencyContact(**item) for item in json.loads(row["emergency_contacts_json"])
        ],
        avatar_url=row["avatar_url"],
    )


class UserRepository:
    def create_seed_user(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str,
        license_type: str,
        home_port: str,
        boat_name: str,
    ) -> FishermanProfilePublic:
        existing = self.get_user_credentials(email)
        if existing is not None:
            return self.get_user_by_id(existing["id"])

        user_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    id, email, password_hash, full_name, license_number, license_type, home_port,
                    boat_name, boat_length_m, engine_hp, fuel_capacity_l,
                    fuel_consumption_l_per_hour, fishing_gears_json, target_species_json,
                    emergency_contacts_json, avatar_url, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    email.lower(),
                    password_hash,
                    full_name,
                    "ADMIN-DEMO",
                    license_type,
                    home_port,
                    boat_name,
                    8.5,
                    180,
                    260.0,
                    24.0,
                    _serialize_list(["ligne"]),
                    _serialize_list(["poulpe"]),
                    _serialize_contacts([]),
                    None,
                    now,
                    now,
                ),
            )
        return self.get_user_by_id(user_id)

    def create_user(self, payload: FishermanProfileCreate, password_hash: str) -> FishermanProfilePublic:
        user_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    id, email, password_hash, full_name, license_number, license_type, home_port,
                    boat_name, boat_length_m, engine_hp, fuel_capacity_l,
                    fuel_consumption_l_per_hour, fishing_gears_json, target_species_json,
                    emergency_contacts_json, avatar_url, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    payload.email.lower(),
                    password_hash,
                    payload.full_name,
                    payload.license_number,
                    payload.license_type,
                    payload.home_port,
                    payload.boat_name,
                    payload.boat_length_m,
                    payload.engine_hp,
                    payload.fuel_capacity_l,
                    payload.fuel_consumption_l_per_hour,
                    _serialize_list(payload.fishing_gears),
                    _serialize_list(payload.target_species),
                    _serialize_contacts(payload.emergency_contacts),
                    payload.avatar_url,
                    now,
                    now,
                ),
            )
        return self.get_user_by_id(user_id)

    def get_user_credentials(self, email: str) -> dict | None:
        with get_db_connection() as connection:
            row = connection.execute(
                "SELECT id, email, password_hash FROM users WHERE email = ?",
                (email.lower(),),
            ).fetchone()
            if row is None:
                return None
            return {"id": row["id"], "email": row["email"], "password_hash": row["password_hash"]}

    def get_user_by_id(self, user_id: str) -> FishermanProfilePublic:
        with get_db_connection() as connection:
            row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if row is None:
                raise ValueError("User not found")
            return _row_to_profile(row)

    def update_user(self, user_id: str, payload: FishermanProfileUpdate) -> FishermanProfilePublic:
        now = datetime.now(UTC).isoformat()
        with get_db_connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET full_name = ?, license_number = ?, license_type = ?, home_port = ?,
                    boat_name = ?, boat_length_m = ?, engine_hp = ?, fuel_capacity_l = ?,
                    fuel_consumption_l_per_hour = ?, fishing_gears_json = ?, target_species_json = ?,
                    emergency_contacts_json = ?, avatar_url = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    payload.full_name,
                    payload.license_number,
                    payload.license_type,
                    payload.home_port,
                    payload.boat_name,
                    payload.boat_length_m,
                    payload.engine_hp,
                    payload.fuel_capacity_l,
                    payload.fuel_consumption_l_per_hour,
                    _serialize_list(payload.fishing_gears),
                    _serialize_list(payload.target_species),
                    _serialize_contacts(payload.emergency_contacts),
                    payload.avatar_url,
                    now,
                    user_id,
                ),
            )
        return self.get_user_by_id(user_id)

    def create_session(self, user_id: str, token: str) -> None:
        now = datetime.now(UTC).isoformat()
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO user_sessions (token, user_id, created_at, last_used_at)
                VALUES (?, ?, ?, ?)
                """,
                (token, user_id, now, now),
            )

    def get_user_by_session_token(self, token: str) -> FishermanProfilePublic | None:
        with get_db_connection() as connection:
            row = connection.execute(
                """
                SELECT users.* FROM user_sessions
                JOIN users ON users.id = user_sessions.user_id
                WHERE user_sessions.token = ?
                """,
                (token,),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                "UPDATE user_sessions SET last_used_at = ? WHERE token = ?",
                (datetime.now(UTC).isoformat(), token),
            )
            return _row_to_profile(row)

    def delete_session(self, token: str) -> None:
        with get_db_connection() as connection:
            connection.execute("DELETE FROM user_sessions WHERE token = ?", (token,))


user_repository = UserRepository()
