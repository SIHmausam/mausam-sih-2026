import httpx
from pydantic import ValidationError

from app.integrations.personalization.base import (
    PersonalizationProvider,
    PersonalizationProviderResponseError,
    PersonalizationProviderUnavailableError,
)
from app.schemas.personalization import (
    MLPersonalizationRequest,
    MLPersonalizationResponse,
)


class MLAPIPersonalizationProvider(PersonalizationProvider):
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        transport: (httpx.AsyncBaseTransport | None) = None,
    ):
        self.base_url = base_url.rstrip("/")

        self.timeout_seconds = timeout_seconds

        # Mainly useful for tests through
        # httpx.MockTransport.
        self.transport = transport

    async def personalize(
        self,
        request: MLPersonalizationRequest,
    ) -> MLPersonalizationResponse:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    "/personalize",
                    json=request.model_dump(mode="json"),
                )

        except (
            httpx.TimeoutException,
            httpx.RequestError,
        ) as exc:
            raise (
                PersonalizationProviderUnavailableError(
                    "ML personalization service is unavailable"
                )
            ) from exc

        if response.status_code >= 500:
            raise (
                PersonalizationProviderUnavailableError(
                    f"ML personalization service returned {response.status_code}"
                )
            )

        if response.status_code >= 400:
            raise (
                PersonalizationProviderResponseError(
                    "ML personalization request "
                    f"was rejected with "
                    f"{response.status_code}"
                )
            )

        try:
            payload = response.json()

            return MLPersonalizationResponse.model_validate(payload)

        except (
            ValueError,
            ValidationError,
        ) as exc:
            raise (
                PersonalizationProviderResponseError(
                    "ML personalization service returned an invalid response"
                )
            ) from exc
