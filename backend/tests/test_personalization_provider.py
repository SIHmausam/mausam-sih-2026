import json
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


def build_request() -> MLPersonalizationRequest:
    return MLPersonalizationRequest(
        user_id=str(
            uuid.uuid4()
        ),

        personas=[
            "fitness"
        ],

        weather=MLWeatherFeatures(
            city="Delhi",

            timestamp=datetime(
                2026,
                9,
                1,
                17,
                0,
                tzinfo=UTC,
            ),

            temperature_2m=32.0,
            relative_humidity_2m=65.0,
            dew_point_2m=24.0,
            apparent_temperature=35.0,

            precipitation=0.0,
            rain=0.0,

            weather_code=1,
            cloud_cover=25.0,

            wind_speed_10m=12.0,
            wind_direction_10m=180.0,
            wind_gusts_10m=18.0,

            soil_moisture_0_to_7cm=0.31,
            soil_moisture_7_to_28cm=0.32,
            soil_moisture_28_to_100cm=0.35,
            soil_moisture_100_to_255cm=0.40,

            soil_temperature_0_to_7cm=28.0,
            soil_temperature_7_to_28cm=27.0,
            soil_temperature_28_to_100cm=26.0,
            soil_temperature_100_to_255cm=25.0,

            et0_fao_evapotranspiration=0.15,

            precipitation_hours=0.0,
            precipitation_probability=20.0,

            showers=0.0,

            visibility=10000.0,

            european_aqi=51.0,
            us_aqi=82.0,

            uv_index=6.0,
            uv_index_clear_sky=7.0,

            pm2_5=23.0,
            pm10=40.0,

            nitrogen_dioxide=12.0,
            sulphur_dioxide=5.0,
            carbon_monoxide=280.0,
            ozone=70.0,

            wave_height=None,
            wave_direction=None,
            wave_period=None,

            swell_wave_height=None,
            swell_wave_direction=None,
            swell_wave_period=None,

            sea_level_height_msl=None,
            sea_surface_temperature=None,

            marine_data_available=False,

            sunrise=datetime(
                2026,
                9,
                1,
                6,
                0,
                tzinfo=UTC,
            ),

            sunset=datetime(
                2026,
                9,
                1,
                18,
                30,
                tzinfo=UTC,
            ),

            is_daylight=True,
        ),
    )


@pytest.mark.asyncio
async def test_ml_provider_returns_ranking():
    cards = [
        "temperature",
        "weather_conditions",
        "humidity",
        "rain_forecast",
        "wind",
        "air_quality",
        "uv_allergy",
        "running_conditions",
    ]

    async def handler(
        request: httpx.Request,
    ):
        assert (
            request.url.path
            == "/personalize"
        )

        request_payload = json.loads(
            request.content
        )

        assert request_payload[
            "personas"
        ] == [
            "fitness"
        ]

        assert (
            "persona"
            not in request_payload
        )

        return httpx.Response(
            200,
            json={
                "city": "Delhi",

                "personas": [
                    "fitness"
                ],

                "cards": [
                    {
                        "rank": index + 1,
                        "card": card,
                        "score": (
                            0.9
                            - index * 0.05
                        ),
                        "insight": (
                            "Test insight"
                        ),
                    }
                    for index, card
                    in enumerate(cards)
                ],
            },
        )

    provider = (
        MLAPIPersonalizationProvider(
            base_url=(
                "http://ml-service:8001"
            ),
            timeout_seconds=5.0,
            transport=httpx.MockTransport(
                handler
            ),
        )
    )

    response = await provider.personalize(
        build_request()
    )

    assert len(
        response.cards
    ) == 8

    assert (
        response.personas
        == ["fitness"]
    )

    assert (
        response.cards[0].card
        == "temperature"
    )

    assert (
        response.cards[5].card
        == "air_quality"
    )


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

    provider = (
        MLAPIPersonalizationProvider(
            base_url=(
                "http://ml-service:8001"
            ),
            timeout_seconds=5.0,
            transport=httpx.MockTransport(
                handler
            ),
        )
    )

    with pytest.raises(
        PersonalizationProviderResponseError
    ):
        await provider.personalize(
            build_request()
        )


@pytest.mark.asyncio
async def test_ml_provider_handles_server_error():
    async def handler(
        request: httpx.Request,
    ):
        return httpx.Response(
            500,
        )

    provider = (
        MLAPIPersonalizationProvider(
            base_url=(
                "http://ml-service:8001"
            ),
            timeout_seconds=5.0,
            transport=httpx.MockTransport(
                handler
            ),
        )
    )

    with pytest.raises(
        PersonalizationProviderUnavailableError
    ):
        await provider.personalize(
            build_request()
        )


@pytest.mark.asyncio
async def test_ml_provider_forwards_interaction():
    captured = {}

    async def handler(
        request: httpx.Request,
    ):
        captured["path"] = (
            request.url.path
        )

        captured["body"] = json.loads(
            request.content
        )

        return httpx.Response(
            200,
            json={
                "status": "success",
            },
        )

    provider = (
        MLAPIPersonalizationProvider(
            base_url=(
                "http://ml-service:8001"
            ),
            timeout_seconds=5.0,
            transport=httpx.MockTransport(
                handler
            ),
        )
    )

    interaction_request = (
        MLInteractionRequest(
            user_id=str(
                uuid.uuid4()
            ),

            card_id=(
                "rain_forecast"
            ),

            action="click",

            timestamp=datetime.now(
                UTC
            ),

            position=2,

            session_id=(
                "session-123"
            ),
        )
    )

    await provider.record_interaction(
        interaction_request
    )

    assert (
        captured["path"]
        == "/interaction"
    )

    assert (
        captured["body"][
            "card_id"
        ]
        == "rain_forecast"
    )

    assert (
        captured["body"][
            "action"
        ]
        == "click"
    )

    assert (
        captured["body"][
            "position"
        ]
        == 2
    )

    assert (
        captured["body"][
            "session_id"
        ]
        == "session-123"
    )