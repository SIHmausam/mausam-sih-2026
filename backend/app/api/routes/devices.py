import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.device import (
    DeviceListResponse,
    DeviceRegistrationRequest,
    DeviceResponse,
)
from app.services.device_service import (
    DeviceNotFoundError,
    DeviceService,
)

router = APIRouter(
    prefix="/devices",
    tags=["devices"],
)


@router.post(
    "/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
)
async def register_device(
    payload: DeviceRegistrationRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> DeviceResponse:
    service = DeviceService(session)

    device = await service.register_device(
        user_id=current_user.id,
        registration_id=(payload.registration_id),
        registration_type=(payload.registration_type),
        platform=payload.platform,
        device_name=payload.device_name,
    )

    return DeviceResponse.model_validate(device)


@router.get(
    "",
    response_model=DeviceListResponse,
)
async def list_devices(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> DeviceListResponse:
    service = DeviceService(session)

    devices = await service.list_devices(user_id=current_user.id)

    return DeviceListResponse(
        devices=[DeviceResponse.model_validate(device) for device in devices]
    )


@router.delete(
    "/{device_id}",
    status_code=(status.HTTP_204_NO_CONTENT),
)
async def unregister_device(
    device_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> Response:
    service = DeviceService(session)

    try:
        await service.unregister_device(
            user_id=current_user.id,
            device_id=device_id,
        )

    except DeviceNotFoundError:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail=("Device registration not found"),
        ) from None

    return Response(status_code=(status.HTTP_204_NO_CONTENT))
