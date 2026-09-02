import uuid
from datetime import (
    UTC,
    date,
    datetime,
)
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.dependencies.auth import (
    get_current_user,
)
from app.dependencies.providers import (
    get_homepage_service,
)
from app.models.user import User
from app.schemas.homepage import (
    HomepageResponse,
)
from app.services.homepage_service import (
    HomepageLocationNotFoundError,
    HomepageService,
)
from app.services.personalization_service import (
    PersonalizationPersonaMissingError,
    PersonalizationPreferencesNotFoundError,
)

router = APIRouter(
    prefix="/homepage",
    tags=["homepage"],
)


@router.get(
    "",
    response_model=HomepageResponse,
)
async def get_homepage(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    service: Annotated[
        HomepageService,
        Depends(get_homepage_service),
    ],
    location_id: uuid.UUID | None = None,
    target_date: date | None = None,
):
    resolved_date = target_date if target_date is not None else datetime.now(UTC).date()

    try:
        return await service.get_homepage(
            user_id=current_user.id,
            target_date=resolved_date,
            location_id=location_id,
        )

    except HomepageLocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except (
        PersonalizationPreferencesNotFoundError,
        PersonalizationPersonaMissingError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
