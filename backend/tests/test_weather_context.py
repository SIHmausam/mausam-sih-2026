import pytest

from app.schemas.air_quality import (
    CurrentAirQualityResponse,
)
from app.schemas.weather import (
    AgricultureContextResponse,
    CurrentWeatherResponse,
    DailyWeatherItem,
    DailyWeatherResponse,
    HourlyWeatherItem,
    HourlyWeatherResponse,
)
from app.services.weather_context_service import (
    WeatherContextService,
)


class FakeWeatherService:
    def __init__(self):
        self.current_calls = 0
        self.hourly_calls = 0
        self.daily_calls = 0
        self.agriculture_calls = 0

    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> CurrentWeatherResponse:
        self.current_calls += 1

        return CurrentWeatherResponse(
            latitude=latitude,
            longitude=longitude,
            temperature=31.0,
            apparent_temperature=35.0,
            humidity=68.0,
            precipitation=1.0,
            rain=0.8,
            weather_code=61,
            wind_speed=12.0,
            is_daylight=True,
        )

    async def get_hourly(
        self,
        latitude: float,
        longitude: float,
    ) -> HourlyWeatherResponse:
        self.hourly_calls += 1

        return HourlyWeatherResponse(
            latitude=latitude,
            longitude=longitude,
            hourly=[
                HourlyWeatherItem(
                    time="2026-08-31T13:00",
                    temperature=31.0,
                    apparent_temperature=35.0,
                    humidity=68.0,
                    precipitation=1.0,
                    rain=0.8,
                    rain_probability=70.0,
                    weather_code=61,
                    wind_speed=12.0,
                    visibility=12000.0,
                )
            ],
        )

    async def get_daily(
        self,
        latitude: float,
        longitude: float,
    ) -> DailyWeatherResponse:
        self.daily_calls += 1

        return DailyWeatherResponse(
            latitude=latitude,
            longitude=longitude,
            daily=[
                DailyWeatherItem(
                    date="2026-08-31",
                    weather_code=61,
                    temperature_max=34.0,
                    temperature_min=26.0,
                    apparent_temperature_max=39.0,
                    apparent_temperature_min=28.0,
                    sunrise="2026-08-31T05:58",
                    sunset="2026-08-31T18:40",
                    precipitation_sum=5.0,
                    rain_sum=4.5,
                    rain_probability_max=80.0,
                    wind_speed_max=18.0,
                )
            ],
        )

    async def get_agriculture_context(
        self,
        latitude: float,
        longitude: float,
    ) -> AgricultureContextResponse:
        self.agriculture_calls += 1

        return AgricultureContextResponse(
            latitude=latitude,
            longitude=longitude,
            surface_soil_moisture=0.32,
            evapotranspiration=0.18,
            vapour_pressure_deficit=0.9,
        )


class FakeAirQualityService:
    def __init__(self):
        self.current_calls = 0

    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> CurrentAirQualityResponse:
        self.current_calls += 1

        return CurrentAirQualityResponse(
            latitude=latitude,
            longitude=longitude,
            aqi=82.0,
            aqi_standard="us",
            us_aqi=82.0,
            european_aqi=47.0,
            pm2_5=22.1,
            pm10=39.4,
            nitrogen_dioxide=12.3,
            sulphur_dioxide=5.4,
            carbon_monoxide=180.2,
            ozone=75.6,
            uv_index=5.1,
        )


@pytest.mark.asyncio
async def test_weather_context_combines_environmental_data():
    weather_service = FakeWeatherService()
    air_quality_service = FakeAirQualityService()

    service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
    )

    response = await service.get_context(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert response.latitude == 28.6139
    assert response.longitude == 77.2090

    assert response.current.temperature == 31.0
    assert response.current.humidity == 68.0

    assert len(response.hourly) == 1
    assert response.hourly[0].rain_probability == 70.0

    assert len(response.daily) == 1
    assert response.daily[0].temperature_max == 34.0

    assert response.agriculture is not None
    assert response.agriculture.surface_soil_moisture == 0.32

    assert response.air_quality is not None

    assert response.air_quality.aqi == 82.0
    assert response.air_quality.us_aqi == 82.0
    assert response.air_quality.european_aqi == 47.0

    assert response.air_quality.pm2_5 == 22.1
    assert response.air_quality.pm10 == 39.4

    assert response.air_quality.nitrogen_dioxide == 12.3
    assert response.air_quality.sulphur_dioxide == 5.4
    assert response.air_quality.carbon_monoxide == 180.2

    assert response.air_quality.ozone == 75.6
    assert response.air_quality.uv_index == 5.1

    assert weather_service.current_calls == 1
    assert weather_service.hourly_calls == 1
    assert weather_service.daily_calls == 1
    assert weather_service.agriculture_calls == 1

    assert air_quality_service.current_calls == 1
