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
            "ML personalization features are unavailable: "
            + ", ".join(
                missing_fields
            )
        )


class MLFeatureBuilder:
    @staticmethod
    def _find_daily_item(
        context: WeatherContextResponse,
    ) -> DailyWeatherItem | None:
        observed_at = (
            context.current.observed_at
        )

        if observed_at is None:
            return None

        target_date = (
            observed_at.date().isoformat()
        )

        for item in context.daily:
            if item.date == target_date:
                return item

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
        observed_at = (
            context.current.observed_at
        )

        if observed_at is None:
            raise MLFeatureUnavailableError(
                ["timestamp"]
            )

        air_quality = (
            context.air_quality
        )

        agriculture = (
            context.agriculture
        )

        daily = (
            MLFeatureBuilder
            ._find_daily_item(
                context
            )
        )

        values = {
            "temperature_2m": (
                context.current.temperature
            ),

            "relative_humidity_2m": (
                context.current.humidity
            ),

            "dew_point_2m": (
                context.current.dew_point
            ),

            "apparent_temperature": (
                context.current
                .apparent_temperature
            ),

            "precipitation": (
                context.current.precipitation
            ),

            "rain": (
                context.current.rain
            ),

            "weather_code": (
                context.current.weather_code
            ),

            "cloud_cover": (
                context.current.cloud_cover
            ),

            "wind_speed_10m": (
                context.current.wind_speed
            ),

            "wind_direction_10m": (
                context.current.wind_direction
            ),

            "wind_gusts_10m": (
                context.current.wind_gusts
            ),

            "soil_moisture_0_to_7cm": (
                agriculture.surface_soil_moisture
                if agriculture
                else None
            ),

            "soil_moisture_7_to_28cm": (
                agriculture.soil_moisture_7_to_28cm
                if agriculture
                else None
            ),

            "soil_moisture_28_to_100cm": (
                agriculture.soil_moisture_28_to_100cm
                if agriculture
                else None
            ),

            "soil_moisture_100_to_255cm": (
                agriculture.soil_moisture_100_to_255cm
                if agriculture
                else None
            ),

            "soil_temperature_0_to_7cm": (
                agriculture.soil_temperature_0_to_7cm
                if agriculture
                else None
            ),

            "soil_temperature_7_to_28cm": (
                agriculture.soil_temperature_7_to_28cm
                if agriculture
                else None
            ),

            "soil_temperature_28_to_100cm": (
                agriculture.soil_temperature_28_to_100cm
                if agriculture
                else None
            ),

            "soil_temperature_100_to_255cm": (
                agriculture.soil_temperature_100_to_255cm
                if agriculture
                else None
            ),

            "et0_fao_evapotranspiration": (
                agriculture.evapotranspiration
                if agriculture
                else None
            ),

            "precipitation_hours": (
                daily.precipitation_hours
                if daily
                else None
            ),

            "precipitation_probability": (
                context.current.rain_probability
            ),

            "showers": (
                context.current.showers
            ),

            "visibility": (
                context.current.visibility
            ),

            "european_aqi": (
                air_quality.european_aqi
                if air_quality
                else None
            ),

            "us_aqi": (
                air_quality.us_aqi
                if air_quality
                else None
            ),

            "uv_index": (
                air_quality.uv_index
                if air_quality
                else None
            ),

            "uv_index_clear_sky": (
                (
                    air_quality
                    .uv_index_clear_sky
                )
                if air_quality
                else None
            ),

            "pm2_5": (
                air_quality.pm2_5
                if air_quality
                else None
            ),

            "pm10": (
                air_quality.pm10
                if air_quality
                else None
            ),

            "nitrogen_dioxide": (
                air_quality.nitrogen_dioxide
                if air_quality
                else None
            ),

            "sulphur_dioxide": (
                air_quality.sulphur_dioxide
                if air_quality
                else None
            ),

            "carbon_monoxide": (
                air_quality.carbon_monoxide
                if air_quality
                else None
            ),

            "ozone": (
                air_quality.ozone
                if air_quality
                else None
            ),

            "sunrise": (
                daily.sunrise
                if daily
                else None
            ),

            "sunset": (
                daily.sunset
                if daily
                else None
            ),

            "is_daylight": (
                context.current.is_daylight
            ),
        }

        missing_fields = [
            field
            for field
            in ML_REQUIRED_MODEL_FEATURES
            if values[field] is None
        ]

        if missing_fields:
            raise MLFeatureUnavailableError(
                missing_fields
            )

        weather = MLWeatherFeatures(
            city=city,
            timestamp=observed_at,

            temperature_2m=(
                values[
                    "temperature_2m"
                ]
            ),

            relative_humidity_2m=(
                values[
                    "relative_humidity_2m"
                ]
            ),

            dew_point_2m=(
                values[
                    "dew_point_2m"
                ]
            ),

            apparent_temperature=(
                values[
                    "apparent_temperature"
                ]
            ),

            precipitation=(
                values["precipitation"]
            ),

            rain=values["rain"],

            weather_code=(
                values["weather_code"]
            ),

            cloud_cover=(
                values["cloud_cover"]
            ),

            wind_speed_10m=(
                values[
                    "wind_speed_10m"
                ]
            ),

            wind_direction_10m=(
                values[
                    "wind_direction_10m"
                ]
            ),

            wind_gusts_10m=(
                values[
                    "wind_gusts_10m"
                ]
            ),

            soil_moisture_0_to_7cm=(
                values[
                    "soil_moisture_0_to_7cm"
                ]
            ),

            soil_moisture_7_to_28cm=(
                values[
                    "soil_moisture_7_to_28cm"
                ]
            ),

            soil_moisture_28_to_100cm=(
                values[
                    "soil_moisture_28_to_100cm"
                ]
            ),

            soil_moisture_100_to_255cm=(
                values[
                    "soil_moisture_100_to_255cm"
                ]
            ),

            soil_temperature_0_to_7cm=(
                values[
                    "soil_temperature_0_to_7cm"
                ]
            ),

            soil_temperature_7_to_28cm=(
                values[
                    "soil_temperature_7_to_28cm"
                ]
            ),

            soil_temperature_28_to_100cm=(
                values[
                    "soil_temperature_28_to_100cm"
                ]
            ),

            soil_temperature_100_to_255cm=(
                values[
                    "soil_temperature_100_to_255cm"
                ]
            ),

            et0_fao_evapotranspiration=(
                values[
                    "et0_fao_evapotranspiration"
                ]
            ),

            precipitation_hours=(
                values[
                    "precipitation_hours"
                ]
            ),

            precipitation_probability=(
                values[
                    "precipitation_probability"
                ]
            ),

            showers=(
                values["showers"]
            ),

            visibility=(
                values["visibility"]
            ),

            european_aqi=(
                values["european_aqi"]
            ),

            us_aqi=(
                values["us_aqi"]
            ),

            uv_index=(
                values["uv_index"]
            ),

            uv_index_clear_sky=(
                values[
                    "uv_index_clear_sky"
                ]
            ),

            pm2_5=(
                values["pm2_5"]
            ),

            pm10=(
                values["pm10"]
            ),

            nitrogen_dioxide=(
                values[
                    "nitrogen_dioxide"
                ]
            ),

            sulphur_dioxide=(
                values[
                    "sulphur_dioxide"
                ]
            ),

            carbon_monoxide=(
                values[
                    "carbon_monoxide"
                ]
            ),

            ozone=(
                values["ozone"]
            ),

            # Marine provider is not integrated yet.
            wave_height=None,
            wave_direction=None,
            wave_period=None,

            swell_wave_height=None,
            swell_wave_direction=None,
            swell_wave_period=None,

            sea_level_height_msl=None,
            sea_surface_temperature=None,

            marine_data_available=False,

            sunrise=(
                values["sunrise"]
            ),

            sunset=(
                values["sunset"]
            ),

            is_daylight=(
                values[
                    "is_daylight"
                ]
            ),
        )

        return MLPersonalizationRequest(
            user_id=str(
                user_id
            ),

            personas=[
                ML_PERSONA_MAP[
                    persona
                ]
            ],

            weather=weather,
        )