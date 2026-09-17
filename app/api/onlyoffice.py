# app/api/onlyoffice.py

from fastapi import APIRouter, HTTPException

from app.models.document import utc_now

router = APIRouter(
    prefix="/onlyoffice",
    tags=["ONLYOFFICE"],
)

minio_service = None
redis_service = None
onlyoffice_service = None


@router.post("/callback/{document_id}")
async def onlyoffice_callback(
    document_id: str,
    payload: dict,
):

    print("=" * 60)
    print("ONLYOFFICE CALLBACK")
    print("Document:", document_id)
    print("Payload:", payload)
    print("=" * 60)

    document = redis_service.get_document(
        document_id
    )

    if not document:

        print(
            "Document not found:",
            document_id,
        )

        return {
            "error": 1
        }

    status = payload.get("status")

    print(
        "ONLYOFFICE status:",
        status
    )

    # status 6 = force save
    # status 2 = normal save after editing
    if status not in (2, 6):

        print(
            "Nothing to save."
        )

        return {
            "error": 0
        }

    callback_url = payload.get("url")

    if not callback_url:

        print(
            "ERROR: ONLYOFFICE did not send URL"
        )

        return {
            "error": 1
        }

    try:

        print(
            "Downloading updated DOCX..."
        )

        file_bytes = (
            await onlyoffice_service
            .download_callback_file(
                callback_url
            )
        )

        print(
            "Downloaded:",
            len(file_bytes),
            "bytes"
        )

        if not file_bytes:

            print(
                "ERROR: empty document"
            )

            return {
                "error": 1
            }

        # ------------------------------------------------
        # IMPORTANT
        #
        # Overwrite the existing MinIO object.
        #
        # NO versioning.
        # NO v1.
        # NO v2.
        # ------------------------------------------------

        minio_service.upload_bytes(
            file_bytes,
            document.s3_key,
            document.content_type,
        )

        print(
            "Document overwritten in MinIO:"
        )

        print(
            document.s3_key
        )

        # Update Redis metadata
        document.updated_at = utc_now()

        redis_service.save_document(
            document
        )

        print(
            "SYNC SUCCESS"
        )

        return {
            "error": 0
        }

    except Exception as exc:

        print(
            "SYNC ERROR:",
            repr(exc)
        )

        return {
            "error": 1
        }