from enum import StrEnum


class UserPersonaType(StrEnum):
    FARMER = "farmer"
    TRAVELLER = "traveller"
    HEALTH = "health"


class TemperatureUnit(StrEnum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


class WeatherInterest(StrEnum):
    RAINFALL = "rainfall"
    AQI = "aqi"
    HUMIDITY = "humidity"
    WIND = "wind"
    UV = "uv"
    TEMPERATURE = "temperature"
    VISIBILITY = "visibility"
    SOIL_MOISTURE = "soil_moisture"


class ActivityContext(StrEnum):
    FARMING = "farming"
    IRRIGATION = "irrigation"
    TRAVEL = "travel"
    COMMUTE = "commute"
    OUTDOOR_HEALTH = "outdoor_health"
    GENERAL = "general"