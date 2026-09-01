import uuid
from datetime import (
    UTC,
    datetime,
)
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.dependencies.providers import (
    get_homepage_service,
)
from app.main import app
from app.schemas.homepage import (
    HomepageLocation,
    HomepageResponse,
    HomepageWeatherSummary,
)
from app.schemas.personalization import (
    PersonalizationResult,
    PersonalizedCard,
)
from app.schemas.routine import (
    MyDayResponse,
)
from app.schemas.weather import (
    CurrentWeatherResponse,
)


def build_homepage_response():
    now = datetime.now(UTC)

    return HomepageResponse(
        session_id=str(uuid.uuid4()),
        generated_at=now,
        location=HomepageLocation(
            id=uuid.uuid4(),
            label="Home",
            city="Delhi",
            latitude=28.6139,
            longitude=77.2090,
            location_type="home",
        ),
        has_safety_override=False,
        alerts=[],
        weather=HomepageWeatherSummary(
            current=CurrentWeatherResponse(
                latitude=28.6139,
                longitude=77.2090,
                observed_at=now,
                temperature=30.0,
                apparent_temperature=32.0,
                humidity=60.0,
                precipitation=0.0,
                rain=0.0,
                weather_code=1,
                wind_speed=10.0,
                is_daylight=True,
            ),
        ),
        my_day=MyDayResponse(
            date=now.date(),
            routines=[],
        ),
        personalization=(
            PersonalizationResult(
                location_id=str(uuid.uuid4()),
                city="Delhi",
                persona="health",
                source="fallback",
                cards=[
                    PersonalizedCard(
                        rank=index,
                        card=card,
                    )
                    for index, card in enumerate(
                        [
                            "aqi",
                            "uv",
                            "temperature",
                            "humidity",
                            "weather_condition",
                            "rainfall",
                            "wind",
                            "soil_moisture",
                        ],
                        start=1,
                    )
                ],
            )
        ),
    )


@pytest.mark.asyncio
async def test_homepage_endpoint(
    client: AsyncClient,
):
    service = AsyncMock()

    service.get_homepage.return_value = build_homepage_response()

    app.dependency_overrides[get_homepage_service] = lambda: service

    try:
        response = await client.get("/api/v1/homepage")

        assert response.status_code == 200

        data = response.json()

        assert data["location"]["city"] == "Delhi"

        assert data["weather"]["current"]["temperature"] == 30.0

        assert len(data["personalization"]["cards"]) == 8

        assert data["session_id"]

        service.get_homepage.assert_awaited_once()

    finally:
        app.dependency_overrides.pop(
            get_homepage_service,
            None,
        )
