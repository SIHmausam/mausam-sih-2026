from app.core.enums import (
    CardType,
    UserPersonaType,
)

ML_PERSONA_MAP: dict[
    UserPersonaType,
    str,
] = {
    UserPersonaType.FARMER: "farmer",
    UserPersonaType.TRAVELLER: "traveler",
    UserPersonaType.HEALTH: "fitness",
}


ML_CARD_MAP: dict[
    CardType,
    str,
] = {
    CardType.AQI: "aqi",
    CardType.UV: "uv",
    CardType.TEMPERATURE: "temperature",
    CardType.HUMIDITY: "humidity",
    CardType.RAINFALL: "rain",
    CardType.WIND: "wind",
    CardType.SOIL_MOISTURE: "soil_moisture",
    CardType.WEATHER_CONDITION: ("weather_condition"),
}


ML_ENVIRONMENT_FEATURES: tuple[str, ...] = (
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
)


ML_CATEGORICAL_FEATURES: tuple[str, ...] = (
    "city",
    "persona",
    "card",
)
