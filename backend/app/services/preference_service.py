import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_activity_preference import UserActivityPreference
from app.models.user_preference import UserPreference
from app.models.user_weather_interest import UserWeatherInterest
from app.repositories.preference_repository import PreferenceRepository
from app.schemas.preferences import (
    NotificationSettings,
    OnboardingRequest,
    PersonalizationSettings,
    PreferencesPatchRequest,
    PreferencesResponse,
)


class PreferencesNotFoundError(Exception):
    """Raised when a user has no stored preferences."""


class OnboardingAlreadyCompletedError(Exception):
    """Raised when a user attempts to complete onboarding more than once."""


class PreferenceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = PreferenceRepository(session)

    async def complete_onboarding(
        self,
        user_id: uuid.UUID,
        payload: OnboardingRequest,
    ) -> PreferencesResponse:
        """
        Complete personalization onboarding for a user.

        The entire operation is transactional:
        preference + personas + interests + activity contexts
        are committed together.
        """

        existing = await self.repository.get_preference(user_id)

        if existing and existing.onboarding_completed:
            raise OnboardingAlreadyCompletedError(
                "Onboarding has already been completed"
            )

        preference = existing or UserPreference(user_id=user_id)

        # Basic preferences
        preference.preferred_language = payload.preferred_language

        preference.temperature_unit = payload.temperature_unit.value

        preference.persona = payload.persona.value

        preference.preferred_start_hour = payload.preferred_start_hour

        preference.preferred_end_hour = payload.preferred_end_hour

        # Notification preferences
        preference.official_alerts_enabled = payload.notifications.official_alerts

        preference.routine_alerts_enabled = payload.notifications.routine_alerts

        preference.rain_alerts_enabled = payload.notifications.rain_alerts

        preference.aqi_alerts_enabled = payload.notifications.aqi_alerts

        preference.daily_summary_enabled = payload.notifications.daily_summary

        # Personalization preferences
        preference.personalized_homepage_enabled = (
            payload.personalization.personalized_homepage
        )

        preference.routine_impact_enabled = payload.personalization.routine_impact

        preference.learning_enabled = payload.personalization.learn_from_activity

        preference.onboarding_completed = True

        # Build weather-interest rows
        interests = [
            UserWeatherInterest(
                user_id=user_id,
                interest=interest.value,
                enabled=True,
            )
            for interest in payload.interests
        ]

        # Build activity-context rows
        activities = [
            UserActivityPreference(
                user_id=user_id,
                activity_context=context.value,
            )
            for context in payload.activity_contexts
        ]

        try:
            if existing is None:
                self.repository.add_preference(preference)

            await self.repository.replace_interests(
                user_id,
                interests,
            )

            await self.repository.replace_activity_preferences(
                user_id,
                activities,
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return await self.get_preferences(user_id)

    async def get_preferences(
        self,
        user_id: uuid.UUID,
    ) -> PreferencesResponse:
        """
        Return the complete personalization configuration
        for the authenticated user.
        """

        preference = await self.repository.get_preference(user_id)

        if preference is None:
            raise PreferencesNotFoundError("User preferences not found")

        interests = await self.repository.get_interests(user_id)

        activities = await self.repository.get_activity_preferences(user_id)

        return PreferencesResponse(
            preferred_language=(preference.preferred_language),
            temperature_unit=(preference.temperature_unit),
            preferred_start_hour=(preference.preferred_start_hour),
            preferred_end_hour=(preference.preferred_end_hour),
            persona=preference.persona,
            interests=[item.interest for item in interests if item.enabled],
            activity_contexts=[item.activity_context for item in activities],
            notifications=NotificationSettings(
                official_alerts=(preference.official_alerts_enabled),
                routine_alerts=(preference.routine_alerts_enabled),
                rain_alerts=(preference.rain_alerts_enabled),
                aqi_alerts=(preference.aqi_alerts_enabled),
                daily_summary=(preference.daily_summary_enabled),
            ),
            personalization=PersonalizationSettings(
                personalized_homepage=(preference.personalized_homepage_enabled),
                routine_impact=(preference.routine_impact_enabled),
                learn_from_activity=(preference.learning_enabled),
            ),
            onboarding_completed=(preference.onboarding_completed),
        )

    async def update_preferences(
        self,
        user_id: uuid.UUID,
        payload: PreferencesPatchRequest,
    ) -> PreferencesResponse:
        """
        Partially update user preferences.

        Fields that are not supplied remain unchanged.
        If personas/interests/activity_contexts are supplied,
        their respective selections are replaced.
        """

        preference = await self.repository.get_preference(user_id)

        if preference is None:
            raise PreferencesNotFoundError("User preferences not found")

        fields_set = payload.model_fields_set

        try:
            # --------------------------------
            # Basic preferences
            # --------------------------------

            if (
                "preferred_language" in fields_set
                and payload.preferred_language is not None
            ):
                preference.preferred_language = payload.preferred_language

            if (
                "temperature_unit" in fields_set
                and payload.temperature_unit is not None
            ):
                preference.temperature_unit = payload.temperature_unit.value

            # These may intentionally be set to None,
            # allowing the user to clear preferred timing.
            if "preferred_start_hour" in fields_set:
                preference.preferred_start_hour = payload.preferred_start_hour

            if "preferred_end_hour" in fields_set:
                preference.preferred_end_hour = payload.preferred_end_hour

            # --------------------------------
            # Notification preferences
            # --------------------------------

            if payload.notifications is not None:
                notification_fields = payload.notifications.model_fields_set

                if (
                    "official_alerts" in notification_fields
                    and payload.notifications.official_alerts is not None
                ):
                    preference.official_alerts_enabled = (
                        payload.notifications.official_alerts
                    )

                if (
                    "routine_alerts" in notification_fields
                    and payload.notifications.routine_alerts is not None
                ):
                    preference.routine_alerts_enabled = (
                        payload.notifications.routine_alerts
                    )

                if (
                    "rain_alerts" in notification_fields
                    and payload.notifications.rain_alerts is not None
                ):
                    preference.rain_alerts_enabled = payload.notifications.rain_alerts

                if (
                    "aqi_alerts" in notification_fields
                    and payload.notifications.aqi_alerts is not None
                ):
                    preference.aqi_alerts_enabled = payload.notifications.aqi_alerts

                if (
                    "daily_summary" in notification_fields
                    and payload.notifications.daily_summary is not None
                ):
                    preference.daily_summary_enabled = (
                        payload.notifications.daily_summary
                    )

            # --------------------------------
            # Personalization preferences
            # --------------------------------

            if payload.personalization is not None:
                personalization_fields = payload.personalization.model_fields_set

                if (
                    "personalized_homepage" in personalization_fields
                    and payload.personalization.personalized_homepage is not None
                ):
                    preference.personalized_homepage_enabled = (
                        payload.personalization.personalized_homepage
                    )

                if (
                    "routine_impact" in personalization_fields
                    and payload.personalization.routine_impact is not None
                ):
                    preference.routine_impact_enabled = (
                        payload.personalization.routine_impact
                    )

                if (
                    "learn_from_activity" in personalization_fields
                    and payload.personalization.learn_from_activity is not None
                ):
                    preference.learning_enabled = (
                        payload.personalization.learn_from_activity
                    )

            # --------------------------------
            # Personas
            # --------------------------------

            if "persona" in fields_set and payload.persona is not None:
                preference.persona = payload.persona.value

            # --------------------------------
            # Weather interests
            # --------------------------------

            if "interests" in fields_set and payload.interests is not None:
                interests = [
                    UserWeatherInterest(
                        user_id=user_id,
                        interest=interest.value,
                        enabled=True,
                    )
                    for interest in payload.interests
                ]

                await self.repository.replace_interests(
                    user_id,
                    interests,
                )

            # --------------------------------
            # Activity contexts
            # --------------------------------

            if (
                "activity_contexts" in fields_set
                and payload.activity_contexts is not None
            ):
                activities = [
                    UserActivityPreference(
                        user_id=user_id,
                        activity_context=context.value,
                    )
                    for context in payload.activity_contexts
                ]

                await self.repository.replace_activity_preferences(
                    user_id,
                    activities,
                )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return await self.get_preferences(user_id)
