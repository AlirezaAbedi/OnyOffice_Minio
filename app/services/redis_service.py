import json
from typing import Optional

import redis

from app.models.document import DocumentMetadata


class RedisService:
    def __init__(self, host: str, port: int, db: int):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def save_document(self, document: DocumentMetadata) -> None:
        self.client.set(
            f"document:{document.document_id}",
            document.model_dump_json(),
        )

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        value = self.client.get(f"document:{document_id}")
        if not value:
            return None
        return DocumentMetadata.model_validate(json.loads(value))

    def delete_document(self, document_id: str) -> None:
        self.client.delete(f"document:{document_id}")
