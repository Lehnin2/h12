from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.profile import FishermanProfilePublic
from app.services.auth_service import auth_service

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> FishermanProfilePublic:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    return auth_service.get_user_from_token(credentials.credentials)


def get_current_admin(
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> FishermanProfilePublic:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
