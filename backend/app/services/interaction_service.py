import logging
import uuid
from datetime import (
    UTC,
    datetime,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.integrations.personalization.base import (
    PersonalizationProvider,
    PersonalizationProviderError,
)
from app.ml.contracts import (
    ML_CARD_MAP,
)
from app.repositories.interaction_repository import (
    InteractionRepository,
)
from app.repositories.preference_repository import (
    PreferenceRepository,
)
from app.schemas.interaction import (
    InteractionCreateRequest,
)
from app.schemas.personalization import (
    MLInteractionRequest,
)

logger = logging.getLogger(__name__)


class InteractionService:
    def __init__(
        self,
        session: AsyncSession,
        personalization_provider: (PersonalizationProvider),
    ):
        self.session = session

        self.repository = InteractionRepository(session)

        self.preference_repository = PreferenceRepository(session)

        self.personalization_provider = personalization_provider

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        payload: InteractionCreateRequest,
    ):
        occurred_at = datetime.now(UTC)

        interaction = await self.repository.create(
            user_id=user_id,
            card_type=(payload.card_type.value),
            action=payload.action.value,
            position=payload.position,
            session_id=payload.session_id,
            occurred_at=occurred_at,
        )

        # PostgreSQL is authoritative.
        # Commit before attempting any external
        # ML synchronization.
        await self.session.commit()

        await self.session.refresh(interaction)

        preference = await self.preference_repository.get_preference(user_id)

        if preference is None or not preference.learning_enabled:
            return interaction

        ml_request = MLInteractionRequest(
            user_id=str(user_id),
            card_id=ML_CARD_MAP[payload.card_type],
            action=payload.action.value,
            timestamp=occurred_at,
            position=payload.position,
            session_id=payload.session_id,
        )

        try:
            await self.personalization_provider.record_interaction(ml_request)

        except PersonalizationProviderError:
            # Interaction already exists safely
            # in PostgreSQL. ML synchronization
            # must not make the client request fail.
            logger.warning(
                "Failed to forward interaction to ML service",
                exc_info=True,
            )

        return interaction
