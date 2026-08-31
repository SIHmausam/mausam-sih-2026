from app.core.enums import (
    CardType,
    UserPersonaType,
)

# Backend domain values are intentionally different
# from model-training categorical values.
#
# Do not rename persisted backend personas/cards merely
# to match the current ML model.

COLD_START_PERSONA_MAP: dict[
    UserPersonaType,
    str,
] = {
    UserPersonaType.FARMER: "Farmer",
    UserPersonaType.TRAVELLER: "Traveler",
    UserPersonaType.HEALTH: "Fitness",
}


COLD_START_CARD_MAP: dict[
    CardType,
    str,
] = {
    CardType.AQI: "AQI",
    CardType.UV: "UV",
    CardType.TEMPERATURE: "Temperature",
    CardType.HUMIDITY: "Humidity",
    CardType.RAINFALL: "Rain",
    CardType.WIND: "Wind",
    CardType.SOIL_MOISTURE: "Soil Moisture",
    CardType.WEATHER_CONDITION: "Weather Condition",
}


COLD_START_ENVIRONMENT_FEATURES: tuple[str, ...] = (
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "weather_code",
    "wind_speed_10m",
    "soil_moisture_0_to_7cm",
    "us_aqi",
    "european_aqi",
    "uv_index",
    "pm2_5",
    "pm10",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "carbon_monoxide",
    "ozone",
    "is_daylight",
    "hour",
    "day_of_week",
    "month",
)


COLD_START_CATEGORICAL_FEATURES: tuple[str, ...] = (
    "city",
    "persona",
    "card",
)
