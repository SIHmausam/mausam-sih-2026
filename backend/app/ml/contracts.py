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
    UserPersonaType.HEALTH: "health_conscious",
    UserPersonaType.FITNESS: "fitness",
    UserPersonaType.SURFER: "surfer",
    UserPersonaType.PARENTS_FAMILIES: "parents_families",
    UserPersonaType.COMMUTER: "commuter",
    UserPersonaType.EVENT_PLANNER: "event_planner",
}


ML_CARD_MAP: dict[
    CardType,
    str,
] = {
    CardType.AQI: "air_quality",
    CardType.UV: "uv_allergy",
    CardType.TEMPERATURE: "temperature",
    CardType.HUMIDITY: "humidity",
    CardType.RAINFALL: "rain_forecast",
    CardType.WIND: "wind",
    CardType.SOIL_MOISTURE: "farm_garden",
    CardType.WEATHER_CONDITION: "weather_conditions",
}


ML_CARD_REVERSE_MAP: dict[
    str,
    CardType,
] = {
    ml_card: backend_card
    for backend_card, ml_card
    in ML_CARD_MAP.items()
}


ML_REQUIRED_MODEL_FEATURES: tuple[str, ...] = (
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",

    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "soil_moisture_28_to_100cm",
    "soil_moisture_100_to_255cm",

    "soil_temperature_0_to_7cm",
    "soil_temperature_7_to_28cm",
    "soil_temperature_28_to_100cm",
    "soil_temperature_100_to_255cm",

    "et0_fao_evapotranspiration",

    "precipitation_hours",
    "precipitation_probability",
    "showers",
    "visibility",

    "european_aqi",
    "us_aqi",
    "uv_index",
    "uv_index_clear_sky",

    "pm2_5",
    "pm10",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "carbon_monoxide",
    "ozone",

    "sunrise",
    "sunset",
    "is_daylight",
)