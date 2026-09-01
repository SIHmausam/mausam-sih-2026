from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import get_db_session

# Import these two from the same locations
# your existing authenticated routes use:
from app.dependencies.auth import get_current_user
from app.dependencies.providers import (
    get_personalization_provider,
)
from app.integrations.personalization.base import (
    PersonalizationProvider,
)
from app.models.user import User
from app.schemas.interaction import (
    InteractionCreateRequest,
    InteractionResponse,
)
from app.services.interaction_service import (
    InteractionService,
)

router = APIRouter(
    prefix="/interactions",
    tags=["interactions"],
)


@router.post(
    "",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_interaction(
    payload: InteractionCreateRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    personalization_provider: Annotated[
        PersonalizationProvider,
        Depends(get_personalization_provider),
    ],
):
    service = InteractionService(
        session=session,
        personalization_provider=(personalization_provider),
    )

    return await service.create(
        user_id=current_user.id,
        payload=payload,
    )
