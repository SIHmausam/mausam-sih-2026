import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.enums import (
    UserPersonaType,
)
from app.integrations.personalization.base import (
    PersonalizationProvider,
    PersonalizationProviderError,
)
from app.ml.contracts import (
    ML_CARD_REVERSE_MAP,
)
from app.ml.feature_builder import (
    MLFeatureBuilder,
    MLFeatureUnavailableError,
)
from app.personalization.fallback import (
    build_fallback_ranking,
)
from app.repositories.location_repository import (
    LocationRepository,
)
from app.repositories.preference_repository import (
    PreferenceRepository,
)
from app.schemas.personalization import (
    PersonalizationResult,
    PersonalizedCard,
)
from app.services.weather_context_service import (
    WeatherContextService,
)


class PersonalizationPreferencesNotFoundError(Exception):
    pass


class PersonalizationPersonaMissingError(Exception):
    pass


class PersonalizationLocationNotFoundError(Exception):
    pass


class PersonalizationService:
    def __init__(
        self,
        session: AsyncSession,
        weather_context_service: (WeatherContextService),
        personalization_provider: (PersonalizationProvider),
    ):
        self.preference_repository = PreferenceRepository(session)

        self.location_repository = LocationRepository(session)

        self.weather_context_service = weather_context_service

        self.personalization_provider = personalization_provider

    async def _resolve_location(
        self,
        user_id: uuid.UUID,
        location_id: uuid.UUID | None,
    ):
        if location_id is not None:
            location = await self.location_repository.get_owned_location(
                location_id=location_id,
                user_id=user_id,
            )

            if location is None:
                raise (PersonalizationLocationNotFoundError("Saved location not found"))

            return location

        location = await self.location_repository.get_primary_for_user(user_id=user_id)

        if location is None:
            raise (
                PersonalizationLocationNotFoundError("Primary saved location not found")
            )

        return location

    @staticmethod
    def _fallback(
        *,
        location,
        persona: UserPersonaType,
    ) -> PersonalizationResult:
        return PersonalizationResult(
            location_id=str(location.id),
            city=location.city,
            persona=persona,
            source="fallback",
            cards=build_fallback_ranking(persona),
        )

    async def personalize(
        self,
        user_id: uuid.UUID,
        location_id: uuid.UUID | None = None,
    ) -> PersonalizationResult:
        preference = await self.preference_repository.get_preference(user_id)

        if preference is None:
            raise (
                PersonalizationPreferencesNotFoundError("User preferences not found")
            )

        if preference.persona is None:
            raise (PersonalizationPersonaMissingError("User persona is not configured"))

        persona = UserPersonaType(preference.persona)

        location = await self._resolve_location(
            user_id=user_id,
            location_id=location_id,
        )

        # User explicitly disabled personalized
        # homepage ranking.
        if not preference.personalized_homepage_enabled:
            return self._fallback(
                location=location,
                persona=persona,
            )

        context = await self.weather_context_service.get_context(
            latitude=location.latitude,
            longitude=location.longitude,
        )

        try:
            ml_request = MLFeatureBuilder.build(
                user_id=user_id,
                city=location.city,
                persona=persona,
                context=context,
            )

            ml_response = await self.personalization_provider.personalize(ml_request)

        except (
            MLFeatureUnavailableError,
            PersonalizationProviderError,
        ):
            return self._fallback(
                location=location,
                persona=persona,
            )

        cards = [
            PersonalizedCard(
                rank=item.rank,
                card=ML_CARD_REVERSE_MAP[item.card],
                score=item.score,
                insight=item.insight,
            )
            for item in ml_response.cards
        ]

        cards.sort(key=lambda item: item.rank)

        return PersonalizationResult(
            location_id=str(location.id),
            city=location.city,
            persona=persona,
            source="ml",
            cards=cards,
        )
