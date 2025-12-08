from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.schemas import ChatMessageRequest, ChatMessageResponse, TaskResponse
from src.domain.exceptions import ValidationError
from src.domain.services.chat_service import ChatService
from src.infrastructure.auth.dependencies import get_current_user_id
from src.infrastructure.dependencies import get_chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    payload: ChatMessageRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        result = await chat_service.create_task_from_message(
            user_id=current_user_id, message=payload.message
        )

        created_task = (
            TaskResponse.model_validate(result.created_task) if result.created_task else None
        )

        return ChatMessageResponse(reply=result.reply, created_task=created_task)

    except (ValidationError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
