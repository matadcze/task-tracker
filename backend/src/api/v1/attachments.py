from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from src.api.schemas import AttachmentListResponse, AttachmentResponse
from src.domain.exceptions import AuthorizationError, NotFoundError, ValidationError
from src.domain.services import AttachmentService
from src.infrastructure.auth.dependencies import get_current_user_id
from src.infrastructure.dependencies import get_attachment_service

router = APIRouter(prefix="/tasks/{task_id}/attachments", tags=["Attachments"])


@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: UUID,
    file: UploadFile = File(...),
    current_user_id: UUID = Depends(get_current_user_id),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    try:
        file_bytes = await file.read()
        created_attachment = await attachment_service.upload_attachment(
            task_id=task_id,
            user_id=current_user_id,
            filename=file.filename or "unnamed",
            file_content=file_bytes,
            mime_type=file.content_type or "application/octet-stream",
        )

        return AttachmentResponse.model_validate(created_attachment)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=AttachmentListResponse)
async def list_attachments(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    try:
        attachments = await attachment_service.list_attachments(task_id, current_user_id)

        return AttachmentListResponse(
            items=[AttachmentResponse.model_validate(att) for att in attachments]
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/{attachment_id}")
async def download_attachment(
    task_id: UUID,
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    try:
        file_path, attachment = await attachment_service.get_attachment_file_path(
            task_id=task_id,
            attachment_id=attachment_id,
            user_id=current_user_id,
        )

        return FileResponse(
            path=file_path,
            filename=attachment.filename,
            media_type=attachment.content_type,
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    task_id: UUID,
    attachment_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    try:
        await attachment_service.delete_attachment(
            task_id=task_id,
            attachment_id=attachment_id,
            user_id=current_user_id,
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
