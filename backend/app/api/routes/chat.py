from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.models.chat import ChatMessageRequest, ChatMessageResponse
from app.models.profile import FishermanProfilePublic
from app.services.chat_service import chat_service

router = APIRouter()


@router.post("/message", response_model=ChatMessageResponse)
def send_chat_message(
    payload: ChatMessageRequest,
    current_user: FishermanProfilePublic = Depends(get_current_user),
) -> ChatMessageResponse:
    return chat_service.reply(payload, current_user)
