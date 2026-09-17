import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response


from app.config import settings
from app.models.document import (
    DocumentMetadata,
    DocumentResponse,
    utc_now,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

# These are assigned by main.py during application startup.
minio_service = None
redis_service = None
onlyoffice_service = None


# ---------------------------------------------------------
# Upload document
# ---------------------------------------------------------
@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    document_id = str(uuid.uuid4())

    filename = Path(file.filename).name

    content_type = (
        file.content_type
        or "application/octet-stream"
    )

    s3_key = f"{document_id}/{filename}"

    data = await file.read()

    minio_service.upload_bytes(
        data,
        s3_key,
        content_type,
    )

    now = utc_now()

    metadata = DocumentMetadata(
        document_id=document_id,
        filename=filename,
        bucket=minio_service.bucket,
        s3_key=s3_key,
        content_type=content_type,
        version=1,
        created_at=now,
        updated_at=now,
    )

    redis_service.save_document(metadata)

    return metadata


# ---------------------------------------------------------
# Get document metadata
# ---------------------------------------------------------
@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(document_id: str):

    document = redis_service.get_document(
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document

## Force Save
@router.post("/{document_id}/force-save")
async def force_save_document(
    document_id: str,
):

    document = redis_service.get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    # This MUST be the same key used when
    # the ONLYOFFICE editor was opened.
    result = await onlyoffice_service.force_save(
        document_id
    )

    return {
        "document_id": document_id,
        "result": result,
    }


# ---------------------------------------------------------
# Download document
# ---------------------------------------------------------
@router.get("/{document_id}/download")
def download_document(document_id: str):

    document = redis_service.get_document(
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    data = minio_service.download_bytes(
        document.s3_key
    )

    return Response(
        content=data,
        media_type=document.content_type,
        headers={
            "Content-Disposition": (
                f'inline; filename="{document.filename}"'
            )
        },
    )


# ---------------------------------------------------------
# ONLYOFFICE editor configuration
# ---------------------------------------------------------
@router.get("/{document_id}/edit")
def edit_document(document_id: str):

    document = redis_service.get_document(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    document_url = (
        f"{settings.internal_api_url}"
        f"/documents/{document_id}/download"
    )

    print("ONLYOFFICE document URL:", document_url)

    config = onlyoffice_service.build_config(
        document_id=document.document_id,
        filename=document.filename,
        document_url=document_url,
    )

    print("ONLYOFFICE configuration:", config)

    return config

# ---------------------------------------------------------
# Delete document
# ---------------------------------------------------------
@router.delete("/{document_id}")
def delete_document(document_id: str):

    document = redis_service.get_document(
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    minio_service.delete(
        document.s3_key
    )

    redis_service.delete_document(
        document_id
    )

    return {
        "message": "Document deleted",
        "document_id": document_id,
    }
