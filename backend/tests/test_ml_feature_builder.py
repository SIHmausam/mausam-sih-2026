import uuid
from datetime import datetime

import pytest

from app.core.enums import (
    UserPersonaType,
)
from app.ml.feature_builder import (
    MLFeatureBuilder,
    MLFeatureUnavailableError,
)
from app.schemas.air_quality import (
    CurrentAirQualityResponse,
)
from app.schemas.weather import (
    AgricultureContextResponse,
    CurrentWeatherResponse,
    DailyWeatherItem,
    WeatherContextResponse,
)


def build_context() -> WeatherContextResponse:
    return WeatherContextResponse(
        latitude=28.6139,
        longitude=77.2090,
        current=CurrentWeatherResponse(
            latitude=28.6139,
            longitude=77.2090,
            observed_at=datetime.fromisoformat("2026-09-01T17:00:00"),
            temperature=32.0,
            apparent_temperature=35.0,
            humidity=65.0,
            precipitation=0.0,
            rain=0.0,
            weather_code=1,
            wind_speed=12.0,
            is_daylight=True,
        ),
        hourly=[],
        daily=[
            DailyWeatherItem(
                date="2026-09-01",
                sunrise=datetime.fromisoformat("2026-09-01T06:00:00"),
                sunset=datetime.fromisoformat("2026-09-01T18:30:00"),
            ),
        ],
        agriculture=(
            AgricultureContextResponse(
                latitude=28.6139,
                longitude=77.2090,
                surface_soil_moisture=0.31,
            )
        ),
        air_quality=(
            CurrentAirQualityResponse(
                latitude=28.6139,
                longitude=77.2090,
                us_aqi=82.0,
                european_aqi=51.0,
                uv_index=6.0,
                pm2_5=23.0,
                pm10=40.0,
                nitrogen_dioxide=12.0,
                sulphur_dioxide=5.0,
                carbon_monoxide=280.0,
                ozone=70.0,
            )
        ),
    )


def test_health_maps_to_fitness():
    request = MLFeatureBuilder.build(
        user_id=uuid.uuid4(),
        city="Delhi",
        persona=UserPersonaType.HEALTH,
        context=build_context(),
    )

    assert request.persona == "fitness"


def test_traveller_maps_to_traveler():
    request = MLFeatureBuilder.build(
        user_id=uuid.uuid4(),
        city="Delhi",
        persona=(UserPersonaType.TRAVELLER),
        context=build_context(),
    )

    assert request.persona == "traveler"


def test_weather_context_maps_to_ml_features():
    request = MLFeatureBuilder.build(
        user_id=uuid.uuid4(),
        city="Delhi",
        persona=UserPersonaType.FARMER,
        context=build_context(),
    )

    weather = request.weather

    assert weather.city == "Delhi"

    assert weather.temperature_2m == 32.0

    assert weather.relative_humidity_2m == 65.0

    assert weather.soil_moisture_0_to_7cm == 0.31

    assert weather.us_aqi == 82.0

    assert weather.pm2_5 == 23.0

    assert weather.is_daylight is True


def test_missing_required_feature_raises():
    context = build_context()

    context.air_quality = None

    with pytest.raises(MLFeatureUnavailableError) as exc:
        MLFeatureBuilder.build(
            user_id=uuid.uuid4(),
            city="Delhi",
            persona=UserPersonaType.HEALTH,
            context=context,
        )

    assert "us_aqi" in (exc.value.missing_fields)

    assert "pm2_5" in (exc.value.missing_fields)
