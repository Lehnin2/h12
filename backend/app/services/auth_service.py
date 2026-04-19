import hashlib
import hmac
import secrets

from fastapi import HTTPException

from app.core.config import settings
from app.models.auth import AuthResponse, LoginRequest
from app.models.profile import FishermanProfileCreate, FishermanProfilePublic, FishermanProfileUpdate
from app.repositories.user_repository import user_repository


class AuthService:
    def _hash_password(self, password: str, salt: bytes | None = None) -> str:
        salt_bytes = salt or secrets.token_bytes(16)
        key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt_bytes,
            n=2**14,
            r=8,
            p=1,
            dklen=32,
        )
        return f"{salt_bytes.hex()}:{key.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        salt_hex, key_hex = stored_hash.split(":")
        candidate = self._hash_password(password, bytes.fromhex(salt_hex)).split(":")[1]
        return hmac.compare_digest(candidate, key_hex)

    def register(self, payload: FishermanProfileCreate) -> AuthResponse:
        existing = user_repository.get_user_credentials(payload.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        password_hash = self._hash_password(payload.password)
        profile = user_repository.create_user(payload, password_hash)
        token = secrets.token_urlsafe(32)
        user_repository.create_session(profile.id, token)
        return AuthResponse(access_token=token, profile=profile)

    def login(self, payload: LoginRequest) -> AuthResponse:
        credentials = user_repository.get_user_credentials(payload.email)
        if credentials is None or not self._verify_password(payload.password, credentials["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        profile = user_repository.get_user_by_id(credentials["id"])
        token = secrets.token_urlsafe(32)
        user_repository.create_session(profile.id, token)
        return AuthResponse(access_token=token, profile=profile)

    def get_user_from_token(self, token: str) -> FishermanProfilePublic:
        profile = user_repository.get_user_by_session_token(token)
        if profile is None:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        return profile

    def update_profile(self, user_id: str, payload: FishermanProfileUpdate) -> FishermanProfilePublic:
        return user_repository.update_user(user_id, payload)

    def logout(self, token: str) -> None:
        user_repository.delete_session(token)

    def ensure_seed_admin(self) -> FishermanProfilePublic | None:
        if not settings.admin_seed_enabled:
            return None
        password_hash = self._hash_password(settings.admin_seed_password)
        return user_repository.create_seed_user(
            email=settings.admin_seed_email,
            password_hash=password_hash,
            full_name="Guardian Admin",
            license_type="artisanal",
            home_port="ghannouch",
            boat_name="Territorial Control",
        )


auth_service = AuthService()
