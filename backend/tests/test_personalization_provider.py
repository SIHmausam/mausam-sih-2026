import uuid
from datetime import (
    UTC,
    datetime,
)

import httpx
import pytest

from app.integrations.personalization.base import (
    PersonalizationProviderResponseError,
    PersonalizationProviderUnavailableError,
)
from app.integrations.personalization.ml_api import (
    MLAPIPersonalizationProvider,
)
from app.schemas.personalization import (
    MLInteractionRequest,
    MLPersonalizationRequest,
    MLWeatherFeatures,
)


def build_request():
    return MLPersonalizationRequest(
        user_id=str(uuid.uuid4()),
        persona="fitness",
        weather=MLWeatherFeatures(
            city="Delhi",
            timestamp=datetime.fromisoformat("2026-09-01T17:00:00"),
            temperature_2m=32.0,
            relative_humidity_2m=65.0,
            apparent_temperature=35.0,
            precipitation=0.0,
            rain=0.0,
            weather_code=1,
            wind_speed_10m=12.0,
            soil_moisture_0_to_7cm=0.31,
            us_aqi=82.0,
            european_aqi=51.0,
            uv_index=6.0,
            pm2_5=23.0,
            pm10=40.0,
            nitrogen_dioxide=12.0,
            sulphur_dioxide=5.0,
            carbon_monoxide=280.0,
            ozone=70.0,
            is_daylight=True,
        ),
    )


@pytest.mark.asyncio
async def test_ml_provider_returns_ranking():
    cards = [
        "aqi",
        "uv",
        "temperature",
        "humidity",
        "rain",
        "wind",
        "soil_moisture",
        "weather_condition",
    ]

    async def handler(
        request: httpx.Request,
    ):
        assert request.url.path == "/personalize"

        return httpx.Response(
            200,
            json={
                "city": "Delhi",
                "persona": "fitness",
                "cards": [
                    {
                        "rank": index + 1,
                        "card": card,
                        "score": (0.9 - index * 0.05),
                        "insight": "Test insight",
                    }
                    for index, card in enumerate(cards)
                ],
            },
        )

    provider = MLAPIPersonalizationProvider(
        base_url=("http://ml-service:8001"),
        timeout_seconds=5.0,
        transport=httpx.MockTransport(handler),
    )

    response = await provider.personalize(build_request())

    assert len(response.cards) == 8

    assert response.cards[0].card == "aqi"


@pytest.mark.asyncio
async def test_ml_provider_rejects_bad_response():
    async def handler(
        request: httpx.Request,
    ):
        return httpx.Response(
            200,
            json={
                "invalid": True,
            },
        )

    provider = MLAPIPersonalizationProvider(
        base_url=("http://ml-service:8001"),
        timeout_seconds=5.0,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(PersonalizationProviderResponseError):
        await provider.personalize(build_request())


@pytest.mark.asyncio
async def test_ml_provider_handles_server_error():
    async def handler(
        request: httpx.Request,
    ):
        return httpx.Response(
            500,
        )

    provider = MLAPIPersonalizationProvider(
        base_url=("http://ml-service:8001"),
        timeout_seconds=5.0,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(PersonalizationProviderUnavailableError):
        await provider.personalize(build_request())


@pytest.mark.asyncio
async def test_ml_provider_forwards_interaction():
    captured = {}

    async def handler(
        request: httpx.Request,
    ):
        captured["path"] = request.url.path

        captured["body"] = request.content.decode()

        return httpx.Response(
            201,
            json={"status": "saved"},
        )

    provider = MLAPIPersonalizationProvider(
        base_url=("http://ml-service:8001"),
        timeout_seconds=5.0,
        transport=httpx.MockTransport(handler),
    )

    request = MLInteractionRequest(
        user_id=str(uuid.uuid4()),
        card_id="rain",
        action="click",
        timestamp=datetime.now(UTC),
        position=2,
        session_id="session-123",
    )

    await provider.record_interaction(request)

    assert captured["path"] == "/interaction"
