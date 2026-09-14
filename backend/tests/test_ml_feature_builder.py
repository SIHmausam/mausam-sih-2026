import uuid
from datetime import (
    UTC,
    datetime,
)

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
    observed_at = datetime(
        2026,
        9,
        1,
        17,
        0,
        tzinfo=UTC,
    )

    sunrise = datetime(
        2026,
        9,
        1,
        6,
        0,
        tzinfo=UTC,
    )

    sunset = datetime(
        2026,
        9,
        1,
        18,
        30,
        tzinfo=UTC,
    )

    return WeatherContextResponse(
        latitude=28.6139,
        longitude=77.2090,

        current=CurrentWeatherResponse(
            latitude=28.6139,
            longitude=77.2090,

            observed_at=observed_at,

            temperature=32.0,
            apparent_temperature=35.0,
            humidity=65.0,
            dew_point=24.0,

            precipitation=0.0,
            rain=0.0,
            showers=0.0,
            rain_probability=20.0,

            weather_code=1,
            cloud_cover=25.0,

            wind_speed=12.0,
            wind_direction=180.0,
            wind_gusts=18.0,

            visibility=10000.0,

            is_daylight=True,
        ),

        hourly=[],

        daily=[
            DailyWeatherItem(
                date="2026-09-01",

                weather_code=1,

                temperature_max=34.0,
                temperature_min=26.0,

                apparent_temperature_max=37.0,
                apparent_temperature_min=28.0,

                sunrise=sunrise,
                sunset=sunset,

                precipitation_sum=0.0,
                rain_sum=0.0,

                precipitation_hours=0.0,

                rain_probability_max=20.0,

                wind_speed_max=18.0,
            ),
        ],

        agriculture=(
            AgricultureContextResponse(
                latitude=28.6139,
                longitude=77.2090,

                surface_soil_moisture=0.31,

                soil_moisture_7_to_28cm=0.32,
                soil_moisture_28_to_100cm=0.35,
                soil_moisture_100_to_255cm=0.40,

                soil_temperature_0_to_7cm=28.0,
                soil_temperature_7_to_28cm=27.0,
                soil_temperature_28_to_100cm=26.0,
                soil_temperature_100_to_255cm=25.0,

                evapotranspiration=0.15,

                vapour_pressure_deficit=0.8,
            )
        ),

        air_quality=(
            CurrentAirQualityResponse(
                latitude=28.6139,
                longitude=77.2090,

                aqi=82.0,
                aqi_standard="us",

                us_aqi=82.0,
                european_aqi=51.0,

                uv_index=6.0,
                uv_index_clear_sky=7.0,

                pm2_5=23.0,
                pm10=40.0,

                nitrogen_dioxide=12.0,
                sulphur_dioxide=5.0,
                carbon_monoxide=280.0,
                ozone=70.0,
            )
        ),
    )


def test_health_maps_to_health_conscious():
    request = MLFeatureBuilder.build(
        user_id=uuid.uuid4(),
        city="Delhi",
        persona=UserPersonaType.HEALTH,
        context=build_context(),
    )

    assert request.personas == [
        "health_conscious"
    ]


def test_traveller_maps_to_traveler():
    request = MLFeatureBuilder.build(
        user_id=uuid.uuid4(),
        city="Delhi",
        persona=UserPersonaType.TRAVELLER,
        context=build_context(),
    )

    assert request.personas == [
        "traveler"
    ]


def test_weather_context_maps_to_ml_features():
    request = MLFeatureBuilder.build(
        user_id=uuid.uuid4(),
        city="Delhi",
        persona=UserPersonaType.FARMER,
        context=build_context(),
    )

    weather = request.weather

    assert request.personas == [
        "farmer"
    ]

    assert weather.city == "Delhi"

    assert weather.temperature_2m == 32.0

    assert weather.relative_humidity_2m == 65.0

    assert weather.dew_point_2m == 24.0

    assert weather.apparent_temperature == 35.0

    assert weather.precipitation == 0.0

    assert weather.rain == 0.0

    assert weather.showers == 0.0

    assert weather.precipitation_probability == 20.0

    assert weather.weather_code == 1

    assert weather.cloud_cover == 25.0

    assert weather.wind_speed_10m == 12.0

    assert weather.wind_direction_10m == 180.0

    assert weather.wind_gusts_10m == 18.0

    assert weather.visibility == 10000.0

    assert weather.soil_moisture_0_to_7cm == 0.31

    assert weather.soil_moisture_7_to_28cm == 0.32

    assert weather.soil_moisture_28_to_100cm == 0.35

    assert weather.soil_moisture_100_to_255cm == 0.40

    assert weather.soil_temperature_0_to_7cm == 28.0

    assert weather.soil_temperature_7_to_28cm == 27.0

    assert weather.soil_temperature_28_to_100cm == 26.0

    assert weather.soil_temperature_100_to_255cm == 25.0

    assert weather.et0_fao_evapotranspiration == 0.15

    assert weather.precipitation_hours == 0.0

    assert weather.us_aqi == 82.0

    assert weather.european_aqi == 51.0

    assert weather.uv_index == 6.0

    assert weather.uv_index_clear_sky == 7.0

    assert weather.pm2_5 == 23.0

    assert weather.pm10 == 40.0

    assert weather.nitrogen_dioxide == 12.0

    assert weather.sulphur_dioxide == 5.0

    assert weather.carbon_monoxide == 280.0

    assert weather.ozone == 70.0

    assert weather.marine_data_available is False

    assert weather.wave_height is None

    assert weather.sea_surface_temperature is None

    assert weather.is_daylight is True


def test_missing_required_feature_raises():
    context = build_context()

    context.air_quality = None

    with pytest.raises(
        MLFeatureUnavailableError
    ) as exc:
        MLFeatureBuilder.build(
            user_id=uuid.uuid4(),
            city="Delhi",
            persona=UserPersonaType.HEALTH,
            context=context,
        )

    assert "us_aqi" in (
        exc.value.missing_fields
    )

    assert "pm2_5" in (
        exc.value.missing_fields
    )

    assert "uv_index_clear_sky" in (
        exc.value.missing_fields
    )