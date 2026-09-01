import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.enums import (
    CardType,
    InteractionAction,
)
from app.integrations.personalization.base import (
    PersonalizationProviderUnavailableError,
)
from app.schemas.interaction import (
    InteractionCreateRequest,
)
from app.services.interaction_service import (
    InteractionService,
)


def create_service():
    session = AsyncMock()
    provider = AsyncMock()

    service = InteractionService(
        session=session,
        personalization_provider=provider,
    )

    # Replace real repositories with mocks.
    service.repository = AsyncMock()
    service.preference_repository = AsyncMock()

    return (
        service,
        session,
        provider,
    )


def build_interaction(
    *,
    card_type: CardType = CardType.AQI,
    action: InteractionAction = (InteractionAction.CLICK),
    position: int = 1,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        card_type=card_type.value,
        action=action.value,
        position=position,
        session_id="session-123",
    )


@pytest.mark.asyncio
async def test_interaction_is_stored():
    (
        service,
        session,
        provider,
    ) = create_service()

    user_id = uuid.uuid4()

    stored_interaction = build_interaction()

    service.repository.create.return_value = stored_interaction

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        learning_enabled=True,
    )

    payload = InteractionCreateRequest(
        card_type="aqi",
        action="click",
        position=1,
        session_id="session-123",
    )

    result = await service.create(
        user_id=user_id,
        payload=payload,
    )

    assert result is stored_interaction

    service.repository.create.assert_awaited_once()

    create_call = service.repository.create.await_args.kwargs

    assert create_call["user_id"] == user_id

    assert create_call["card_type"] == "aqi"

    assert create_call["action"] == "click"

    assert create_call["position"] == 1

    assert create_call["session_id"] == "session-123"

    assert create_call["occurred_at"] is not None

    session.commit.assert_awaited_once()

    session.refresh.assert_awaited_once_with(stored_interaction)

    provider.record_interaction.assert_awaited_once()


@pytest.mark.asyncio
async def test_rainfall_maps_to_ml_rain():
    (
        service,
        _,
        provider,
    ) = create_service()

    service.repository.create.return_value = build_interaction(
        card_type=CardType.RAINFALL,
        position=2,
    )

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        learning_enabled=True,
    )

    payload = InteractionCreateRequest(
        card_type="rainfall",
        action="click",
        position=2,
        session_id="session-rain",
    )

    await service.create(
        user_id=uuid.uuid4(),
        payload=payload,
    )

    provider.record_interaction.assert_awaited_once()

    ml_request = provider.record_interaction.await_args.args[0]

    assert ml_request.card_id == "rain"

    assert ml_request.action == "click"

    assert ml_request.position == 2

    assert ml_request.session_id == "session-rain"


@pytest.mark.asyncio
async def test_learning_disabled_skips_ml():
    (
        service,
        session,
        provider,
    ) = create_service()

    stored_interaction = build_interaction()

    service.repository.create.return_value = stored_interaction

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        learning_enabled=False,
    )

    payload = InteractionCreateRequest(
        card_type="aqi",
        action="view",
        position=1,
        session_id="session-123",
    )

    result = await service.create(
        user_id=uuid.uuid4(),
        payload=payload,
    )

    assert result is stored_interaction

    # Backend still stores the event.
    service.repository.create.assert_awaited_once()

    session.commit.assert_awaited_once()

    # But user opted out of behavioral
    # personalization.
    provider.record_interaction.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_preferences_skips_ml():
    (
        service,
        session,
        provider,
    ) = create_service()

    stored_interaction = build_interaction()

    service.repository.create.return_value = stored_interaction

    service.preference_repository.get_preference.return_value = None

    payload = InteractionCreateRequest(
        card_type="aqi",
        action="expand",
        position=1,
        session_id="session-123",
    )

    result = await service.create(
        user_id=uuid.uuid4(),
        payload=payload,
    )

    assert result is stored_interaction

    session.commit.assert_awaited_once()

    provider.record_interaction.assert_not_awaited()


@pytest.mark.asyncio
async def test_ml_failure_does_not_fail_interaction():
    (
        service,
        session,
        provider,
    ) = create_service()

    stored_interaction = build_interaction(
        card_type=CardType.UV,
    )

    service.repository.create.return_value = stored_interaction

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        learning_enabled=True,
    )

    provider.record_interaction.side_effect = PersonalizationProviderUnavailableError(
        "ML service unavailable"
    )

    payload = InteractionCreateRequest(
        card_type="uv",
        action="expand",
        position=3,
        session_id="session-123",
    )

    result = await service.create(
        user_id=uuid.uuid4(),
        payload=payload,
    )

    # Backend interaction still succeeds.
    assert result is stored_interaction

    service.repository.create.assert_awaited_once()

    # Most important guarantee:
    # PostgreSQL was committed before the
    # external ML call failed.
    session.commit.assert_awaited_once()

    provider.record_interaction.assert_awaited_once()


@pytest.mark.asyncio
async def test_dismiss_interaction_is_forwarded():
    (
        service,
        _,
        provider,
    ) = create_service()

    service.repository.create.return_value = build_interaction(
        card_type=CardType.WIND,
        action=InteractionAction.DISMISS,
        position=4,
    )

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        learning_enabled=True,
    )

    payload = InteractionCreateRequest(
        card_type="wind",
        action="dismiss",
        position=4,
        session_id="session-dismiss",
    )

    await service.create(
        user_id=uuid.uuid4(),
        payload=payload,
    )

    ml_request = provider.record_interaction.await_args.args[0]

    assert ml_request.card_id == "wind"

    assert ml_request.action == "dismiss"

    assert ml_request.position == 4


def test_position_zero_is_rejected():
    with pytest.raises(ValueError):
        InteractionCreateRequest(
            card_type="aqi",
            action="view",
            position=0,
            session_id="session-123",
        )


def test_position_above_eight_is_rejected():
    with pytest.raises(ValueError):
        InteractionCreateRequest(
            card_type="aqi",
            action="view",
            position=9,
            session_id="session-123",
        )


def test_all_interaction_actions_are_valid():
    for action in (
        "view",
        "click",
        "expand",
        "dismiss",
    ):
        payload = InteractionCreateRequest(
            card_type="temperature",
            action=action,
            position=1,
            session_id="session-123",
        )

        assert payload.action.value == action
