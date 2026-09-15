from enum import StrEnum


class UserPersonaType(StrEnum):
    FARMER = "farmer"
    TRAVELLER = "traveller"
    HEALTH = "health"

    FITNESS = "fitness"
    SURFER = "surfer"
    PARENTS_FAMILIES = "parents_families"
    COMMUTER = "commuter"
    EVENT_PLANNER = "event_planner"


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

    RUNNING_CONDITIONS = "running_conditions"
    SURF_CONDITIONS = "surf_conditions"
    TIDE_WATER = "tide_water"
    COMMUTE_CONDITIONS = "commute_conditions"
    TRAVEL_CONDITIONS = "travel_conditions"
    FAMILY_SCHOOL = "family_school"
    EVENT_CONDITIONS = "event_conditions"


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


class DevicePlatform(StrEnum):
    ANDROID = "android"
    IOS = "ios"


class PushRegistrationType(StrEnum):
    FID = "fid"
    TOKEN = "token"
