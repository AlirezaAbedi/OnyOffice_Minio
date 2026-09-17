from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx


class OnlyOfficeService:

    def __init__(
        self,
        api_url: str,
        onlyoffice_url: str,
    ):
        self.api_url = api_url.rstrip("/")
        self.onlyoffice_url = onlyoffice_url.rstrip("/")

    @staticmethod
    def file_type(filename: str) -> str:
        extension = Path(filename).suffix.lower().lstrip(".")
        return extension or "docx"

    def build_config(
        self,
        document_id: str,
        filename: str,
        document_url: str,
    ) -> dict[str, Any]:

        return {
            "document": {
                "fileType": self.file_type(filename),

                # IMPORTANT:
                # This key must remain stable while editing.
                "key": document_id,

                "title": filename,
                "url": document_url,
            },

            "editorConfig": {
                "callbackUrl": (
                    f"{self.api_url}"
                    f"/onlyoffice/callback/{document_id}"
                ),

                "mode": "edit",

                "customization": {
                    "autosave": True,
                    "forcesave": True,
                },

                "lang": "en",
            },

            "type": "desktop",
        }

    async def force_save(
        self,
        document_key: str,
    ):

        command_url = f"{self.onlyoffice_url}/command"

        payload = {
            "c": "forcesave",
            "key": document_key,
        }

        print("=" * 60)
        print("FORCE SAVE")
        print("URL:", command_url)
        print("Payload:", payload)
        print("=" * 60)

        async with httpx.AsyncClient(timeout=30) as client:

            response = await client.post(
                command_url,
                json=payload,
            )

            print(
                "FORCE SAVE RESPONSE:",
                response.status_code,
                response.text,
            )

            response.raise_for_status()

            return response.json()
    async def download_callback_file(self, url: str) -> bytes:

        print("Original callback URL:")
        print(url)

        # ONLYOFFICE generates localhost URLs.
        # FastAPI is running in another Docker container,
        # so localhost would point to the FastAPI container.
        if url.startswith("http://localhost:8080"):
            url = url.replace(
                "http://localhost:8080",
                self.onlyoffice_url,
                1,
            )

        elif url.startswith("http://127.0.0.1:8080"):
            url = url.replace(
                "http://127.0.0.1:8080",
                self.onlyoffice_url,
                1,
            )

        print("Internal callback URL:")
        print(url)

        async with httpx.AsyncClient(
            timeout=120,
            follow_redirects=True,
        ) as client:

            response = await client.get(url)

            print(
                "ONLYOFFICE download status:",
                response.status_code,
            )

            response.raise_for_status()

            print(
                "Downloaded bytes:",
                len(response.content),
            )

            return response.content