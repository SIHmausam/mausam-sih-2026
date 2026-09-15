import logging
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
from app.schemas.weather import (
    WeatherContextResponse,
)
from app.services.weather_context_service import (
    WeatherContextService,
)

logger = logging.getLogger(__name__)
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

        # Don't request weather at all when
        # personalization has been disabled.
        if not preference.personalized_homepage_enabled:
            return self._fallback(
                location=location,
                persona=persona,
            )

        context = await self.weather_context_service.get_context(
            latitude=location.latitude,
            longitude=location.longitude,
        )

        return await self.personalize_with_context(
            user_id=user_id,
            location=location,
            context=context,
        )

    async def personalize_at_coordinates(
        self,
        *,
        user_id: uuid.UUID,
        city: str,
        latitude: float,
        longitude: float,
        context: WeatherContextResponse,
    ) -> PersonalizationResult:
        preference = await self.preference_repository.get_preference(user_id)

        if preference is None:
            raise (
                PersonalizationPreferencesNotFoundError("User preferences not found")
            )

        if preference.persona is None:
            raise (PersonalizationPersonaMissingError("User persona is not configured"))

        persona = UserPersonaType(preference.persona)

        personas = await self._get_selected_personas(
            user_id=user_id,
            primary_persona=persona,
        )

        if not preference.personalized_homepage_enabled:
            return PersonalizationResult(
                location_id="",
                city=city,
                persona=persona,
                source="fallback",
                cards=build_fallback_ranking(persona),
            )

        context = await self._attach_marine_if_needed(
            context=context,
            personas=personas,
            latitude=latitude,
            longitude=longitude,
        )

        try:
            ml_request = MLFeatureBuilder.build(
                user_id=user_id,
                city=city,
                personas=personas,
                context=context,
            )

            logger.debug(
                "Sending ML personalization personas: %s",
                ml_request.personas,
            )

            ml_response = await self.personalization_provider.personalize(ml_request)

        except MLFeatureUnavailableError as exc:
            logger.warning(
                "ML personalization skipped because features are missing: %s",
                exc.missing_fields,
            )

            return PersonalizationResult(
                location_id="",
                city=city,
                persona=persona,
                source="fallback",
                cards=build_fallback_ranking(persona),
            )

        except PersonalizationProviderError as exc:
            logger.warning(
                "ML personalization provider failed: %s",
                exc,
            )

            return PersonalizationResult(
                location_id="",
                city=city,
                persona=persona,
                source="fallback",
                cards=build_fallback_ranking(persona),
            )

        cards = self._translate_ml_cards(
            ml_response.cards
        )

        return PersonalizationResult(
            location_id="",
            city=city,
            persona=persona,
            source="ml",
            cards=cards,
        )

    async def personalize_with_context(
        self,
        *,
        user_id: uuid.UUID,
        location,
        context: WeatherContextResponse,
    ) -> PersonalizationResult:
        preference = await self.preference_repository.get_preference(user_id)

        if preference is None:
            raise (
                PersonalizationPreferencesNotFoundError("User preferences not found")
            )

        if preference.persona is None:
            raise (PersonalizationPersonaMissingError("User persona is not configured"))

        persona = UserPersonaType(preference.persona)

        personas = await self._get_selected_personas(
            user_id=user_id,
            primary_persona=persona,
        )

        if not preference.personalized_homepage_enabled:
            return self._fallback(
                location=location,
                persona=persona,
            )

        context = await self._attach_marine_if_needed(
            context=context,
            personas=personas,
            latitude=location.latitude,
            longitude=location.longitude,
        )

        try:
            ml_request = MLFeatureBuilder.build(
                user_id=user_id,
                city=location.city,
                personas=personas,
                context=context,
            )

            logger.debug(
                "Sending ML personalization personas: %s",
                ml_request.personas,
            )

            ml_response = await self.personalization_provider.personalize(ml_request)

        except MLFeatureUnavailableError as exc:
            logger.warning(
                "ML personalization skipped because features are missing: %s",
                exc.missing_fields,
            )

            return self._fallback(
                location=location,
                persona=persona,
            )

        except PersonalizationProviderError as exc:
            logger.warning(
                "ML personalization provider failed: %s",
                exc,
            )

            return self._fallback(
                location=location,
                persona=persona,
            )

        cards = self._translate_ml_cards(
            ml_response.cards
        )

        return PersonalizationResult(
            location_id=str(location.id),
            city=location.city,
            persona=persona,
            source="ml",
            cards=cards,
        )

    async def _attach_marine_if_needed(
        self,
        *,
        context: WeatherContextResponse,
        personas: list[UserPersonaType],
        latitude: float,
        longitude: float,
    ) -> WeatherContextResponse:
        """
        Fetch marine conditions only when the user
        has selected the Surfer persona.

        Marine data is optional. If the provider is
        unavailable or the location is too far from
        a valid sea grid, the original weather context
        is returned unchanged.
        """

        if UserPersonaType.SURFER not in personas:
            return context

        return (
            await self.weather_context_service
            .attach_marine_context(
                context=context,
                latitude=latitude,
                longitude=longitude,
            )
        )

    @staticmethod
    def _translate_ml_cards(
        ml_cards,
    ) -> list[PersonalizedCard]:
        """
        Convert Phase 2 canonical ML cards into
        the Mausam backend card contract.

        Unknown future ML card types are ignored safely.
        """

        translated: list[
            PersonalizedCard
        ] = []

        for item in sorted(
            ml_cards,
            key=lambda value:
                value.rank,
        ):
            backend_card = (
                ML_CARD_REVERSE_MAP.get(
                    item.card
                )
            )

            if backend_card is None:
                continue

            translated.append(
                PersonalizedCard(
                    # Re-rank after filtering unsupported
                    # Phase 2-only cards.
                    rank=(
                        len(translated)
                        + 1
                    ),

                    card=backend_card,

                    score=item.score,

                    insight=item.insight,
                )
            )

        return translated

    async def _get_selected_personas(
        self,
        *,
        user_id: uuid.UUID,
        primary_persona: UserPersonaType,
    ) -> list[UserPersonaType]:
        rows = await self.preference_repository.get_personas(
            user_id
        )

        selected = [
            UserPersonaType(row.persona)
            for row in rows
        ]

        # Legacy safety: existing users may have a primary
        # persona but no user_personas rows.
        if not selected:
            return [
                primary_persona
            ]

        # Keep primary first for deterministic requests.
        ordered = [
            primary_persona
        ]

        ordered.extend(
            persona
            for persona in selected
            if persona != primary_persona
        )

        return ordered
