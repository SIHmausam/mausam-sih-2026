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


class LocationType(StrEnum):
    HOME = "home"
    FARM = "farm"
    DESTINATION = "destination"
    WORK = "work"
    OTHER = "other"


class CardType(StrEnum):
    AQI = "aqi"
    UV = "uv"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    RAINFALL = "rainfall"
    WIND = "wind"
    SOIL_MOISTURE = "soil_moisture"
    WEATHER_CONDITION = "weather_condition"


class InteractionAction(StrEnum):
    VIEW = "view"
    CLICK = "click"
    EXPAND = "expand"
    DISMISS = "dismiss"


class Weekday(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class RoutineImpactLevel(StrEnum):
    SAFE = "safe"
    CAUTION = "caution"
    AVOID = "avoid"

    # Used only when there is not enough
    # environmental/location data to evaluate.
    UNAVAILABLE = "unavailable"


class NotificationType(StrEnum):
    OFFICIAL_ALERT = "official_alert"
    ROUTINE_WARNING = "routine_warning"
    RAIN_ALERT = "rain_alert"
    AQI_ALERT = "aqi_alert"
    DAILY_SUMMARY = "daily_summary"


class NotificationSeverity(StrEnum):
    INFO = "info"
    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"
