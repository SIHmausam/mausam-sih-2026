from pydantic import BaseModel, Field, field_validator

from app.core.enums import (
    ActivityContext,
    TemperatureUnit,
    UserPersonaType,
    WeatherInterest,
)


class NotificationSettings(BaseModel):
    official_alerts: bool = True
    routine_alerts: bool = True
    rain_alerts: bool = True
    aqi_alerts: bool = True
    daily_summary: bool = True


class PersonalizationSettings(BaseModel):
    personalized_homepage: bool = True
    routine_impact: bool = True
    learn_from_activity: bool = True


class OnboardingRequest(BaseModel):
    preferred_language: str = "en"

    temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS

    personas: list[UserPersonaType]

    interests: list[WeatherInterest]

    preferred_start_hour: int | None = Field(
        default=None,
        ge=0,
        le=23,
    )

    preferred_end_hour: int | None = Field(
        default=None,
        ge=0,
        le=23,
    )

    activity_contexts: list[ActivityContext]

    notifications: NotificationSettings = NotificationSettings()

    personalization: PersonalizationSettings = PersonalizationSettings()

    @field_validator(
        "personas",
        "interests",
        "activity_contexts",
    )
    @classmethod
    def reject_duplicates(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Duplicate values are not allowed")

        return value


class PreferencesResponse(BaseModel):
    preferred_language: str
    temperature_unit: TemperatureUnit

    preferred_start_hour: int | None
    preferred_end_hour: int | None

    personas: list[UserPersonaType]
    interests: list[WeatherInterest]
    activity_contexts: list[ActivityContext]

    notifications: NotificationSettings
    personalization: PersonalizationSettings

    onboarding_completed: bool


class NotificationSettingsPatch(BaseModel):
    official_alerts: bool | None = None
    routine_alerts: bool | None = None
    rain_alerts: bool | None = None
    aqi_alerts: bool | None = None
    daily_summary: bool | None = None


class PersonalizationSettingsPatch(BaseModel):
    personalized_homepage: bool | None = None
    routine_impact: bool | None = None
    learn_from_activity: bool | None = None


class PreferencesPatchRequest(BaseModel):
    preferred_language: str | None = None

    temperature_unit: TemperatureUnit | None = None

    preferred_start_hour: int | None = Field(
        default=None,
        ge=0,
        le=23,
    )

    preferred_end_hour: int | None = Field(
        default=None,
        ge=0,
        le=23,
    )

    personas: list[UserPersonaType] | None = None
    interests: list[WeatherInterest] | None = None
    activity_contexts: list[ActivityContext] | None = None

    notifications: NotificationSettingsPatch | None = None
    personalization: PersonalizationSettingsPatch | None = None

    @field_validator(
        "personas",
        "interests",
        "activity_contexts",
    )
    @classmethod
    def reject_duplicate_patch_values(
        cls,
        value,
    ):
        if value is None:
            return value

        if len(value) != len(set(value)):
            raise ValueError("Duplicate values are not allowed")

        return value
