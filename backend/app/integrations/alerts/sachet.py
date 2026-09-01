import httpx

from app.core.config import settings
from app.integrations.alerts.base import (
    AlertProvider,
    CapDocumentResult,
)


class SachetAlertProvider(AlertProvider):
    def __init__(self) -> None:
        self.rss_url = settings.sachet_rss_url
        self.cap_url = settings.sachet_cap_url

    async def get_feed(self) -> str:
        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                self.rss_url,
            )

            response.raise_for_status()

            return response.text

    async def get_cap_document(
        self,
        identifier: str,
        etag: str | None = None,
    ) -> CapDocumentResult:
        headers: dict[str, str] = {}

        if etag is not None:
            headers["If-None-Match"] = etag

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                self.cap_url,
                params={
                    "identifier": identifier,
                },
                headers=headers,
            )

        if response.status_code == 304:
            return CapDocumentResult(
                content=None,
                etag=etag,
                not_modified=True,
            )

        response.raise_for_status()

        return CapDocumentResult(
            content=response.text,
            etag=response.headers.get("ETag"),
        )
