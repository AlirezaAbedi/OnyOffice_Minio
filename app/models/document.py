from datetime import datetime, timezone
from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    bucket: str
    s3_key: str
    content_type: str
    version: int = 1
    created_at: datetime
    updated_at: datetime


class DocumentResponse(DocumentMetadata):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
