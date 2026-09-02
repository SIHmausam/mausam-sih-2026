import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import (
    get_db_session,
)
from app.dependencies.auth import (
    get_current_user,
)
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationReadResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.services.notification_service import (
    NotificationNotFoundError,
    NotificationService,
)

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.get(
    "",
    response_model=NotificationListResponse,
)
async def list_notifications(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    unread_only: bool = False,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
        ),
    ] = 0,
) -> NotificationListResponse:
    service = NotificationService(session)

    notifications = await service.list_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )

    return NotificationListResponse(
        notifications=[
            NotificationResponse.model_validate(notification)
            for notification in notifications
        ]
    )


@router.get(
    "/unread-count",
    response_model=(NotificationUnreadCountResponse),
)
async def get_unread_count(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> NotificationUnreadCountResponse:
    service = NotificationService(session)

    count = await service.get_unread_count(user_id=current_user.id)

    return NotificationUnreadCountResponse(unread_count=count)


@router.patch(
    "/read-all",
    response_model=(NotificationReadAllResponse),
)
async def mark_all_read(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> NotificationReadAllResponse:
    service = NotificationService(session)

    count = await service.mark_all_read(user_id=current_user.id)

    return NotificationReadAllResponse(updated_count=count)


@router.patch(
    "/{notification_id}/read",
    response_model=(NotificationReadResponse),
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> NotificationReadResponse:
    service = NotificationService(session)

    try:
        notification = await service.mark_read(
            user_id=current_user.id,
            notification_id=(notification_id),
        )

    except NotificationNotFoundError:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail=("Notification not found"),
        ) from None

    return NotificationReadResponse(
        id=notification.id,
        is_read=notification.is_read,
        read_at=notification.read_at,
    )
