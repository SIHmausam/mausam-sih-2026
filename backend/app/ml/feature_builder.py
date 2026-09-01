import uuid

from app.core.enums import (
    UserPersonaType,
)
from app.ml.contracts import (
    ML_PERSONA_MAP,
    ML_REQUIRED_MODEL_FEATURES,
)
from app.schemas.personalization import (
    MLPersonalizationRequest,
    MLWeatherFeatures,
)
from app.schemas.weather import (
    DailyWeatherItem,
    WeatherContextResponse,
)


class MLFeatureUnavailableError(ValueError):
    def __init__(
        self,
        missing_fields: list[str],
    ):
        self.missing_fields = missing_fields

        super().__init__(
            "ML personalization features are unavailable: " + ", ".join(missing_fields)
        )


class MLFeatureBuilder:
    @staticmethod
    def _find_daily_item(
        context: WeatherContextResponse,
    ) -> DailyWeatherItem | None:
        observed_at = context.current.observed_at

        if observed_at is None:
            return None

        target_date = observed_at.date().isoformat()

        for item in context.daily:
            if item.date == target_date:
                return item

        # Fallback for providers whose daily
        # date representation differs slightly.
        if context.daily:
            return context.daily[0]

        return None

    @staticmethod
    def build(
        *,
        user_id: uuid.UUID,
        city: str,
        persona: UserPersonaType,
        context: WeatherContextResponse,
    ) -> MLPersonalizationRequest:
        observed_at = context.current.observed_at

        if observed_at is None:
            raise MLFeatureUnavailableError(["timestamp"])

        air_quality = context.air_quality
        agriculture = context.agriculture

        values = {
            "temperature_2m": (context.current.temperature),
            "relative_humidity_2m": (context.current.humidity),
            "apparent_temperature": (context.current.apparent_temperature),
            "precipitation": (context.current.precipitation),
            "rain": (context.current.rain),
            "weather_code": (context.current.weather_code),
            "wind_speed_10m": (context.current.wind_speed),
            "soil_moisture_0_to_7cm": (
                agriculture.surface_soil_moisture if agriculture else None
            ),
            "us_aqi": (air_quality.us_aqi if air_quality else None),
            "european_aqi": (air_quality.european_aqi if air_quality else None),
            "uv_index": (air_quality.uv_index if air_quality else None),
            "pm2_5": (air_quality.pm2_5 if air_quality else None),
            "pm10": (air_quality.pm10 if air_quality else None),
            "nitrogen_dioxide": (air_quality.nitrogen_dioxide if air_quality else None),
            "sulphur_dioxide": (air_quality.sulphur_dioxide if air_quality else None),
            "carbon_monoxide": (air_quality.carbon_monoxide if air_quality else None),
            "ozone": (air_quality.ozone if air_quality else None),
        }

        missing_fields = [
            field for field in ML_REQUIRED_MODEL_FEATURES if values[field] is None
        ]

        if missing_fields:
            raise MLFeatureUnavailableError(missing_fields)

        daily_item = MLFeatureBuilder._find_daily_item(context)

        weather = MLWeatherFeatures(
            city=city,
            timestamp=observed_at,
            temperature_2m=values["temperature_2m"],
            relative_humidity_2m=values["relative_humidity_2m"],
            apparent_temperature=values["apparent_temperature"],
            precipitation=values["precipitation"],
            rain=values["rain"],
            weather_code=values["weather_code"],
            wind_speed_10m=values["wind_speed_10m"],
            soil_moisture_0_to_7cm=values["soil_moisture_0_to_7cm"],
            us_aqi=values["us_aqi"],
            european_aqi=values["european_aqi"],
            uv_index=values["uv_index"],
            pm2_5=values["pm2_5"],
            pm10=values["pm10"],
            nitrogen_dioxide=values["nitrogen_dioxide"],
            sulphur_dioxide=values["sulphur_dioxide"],
            carbon_monoxide=values["carbon_monoxide"],
            ozone=values["ozone"],
            sunrise=(daily_item.sunrise if daily_item else None),
            sunset=(daily_item.sunset if daily_item else None),
            is_daylight=(context.current.is_daylight),
        )

        return MLPersonalizationRequest(
            user_id=str(user_id),
            persona=ML_PERSONA_MAP[persona],
            weather=weather,
        )
