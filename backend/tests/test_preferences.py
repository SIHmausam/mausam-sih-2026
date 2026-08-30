from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.main import app
from app.models.user import User
from app.repositories.preference_repository import (
    PreferenceRepository,
)
from app.schemas.preferences import OnboardingRequest
from app.services.preference_service import (
    PreferenceService,
)


def onboarding_payload() -> dict:
    return {
        "preferred_language": "en",
        "temperature_unit": "celsius",
        "personas": [
            "traveller",
            "health",
        ],
        "interests": [
            "aqi",
            "uv",
            "rainfall",
            "visibility",
        ],
        "preferred_start_hour": 7,
        "preferred_end_hour": 10,
        "activity_contexts": [
            "travel",
            "outdoor_health",
        ],
        "notifications": {
            "official_alerts": True,
            "routine_alerts": True,
            "rain_alerts": True,
            "aqi_alerts": True,
            "daily_summary": True,
        },
        "personalization": {
            "personalized_homepage": True,
            "routine_impact": True,
            "learn_from_activity": True,
        },
    }


@pytest.mark.asyncio
async def test_user_can_complete_onboarding(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/users/onboarding",
        json=onboarding_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["preferred_language"] == "en"
    assert data["temperature_unit"] == "celsius"

    assert set(data["personas"]) == {
        "traveller",
        "health",
    }

    assert data["onboarding_completed"] is True


@pytest.mark.asyncio
async def test_preferences_can_be_read_back(
    client: AsyncClient,
):
    create_response = await client.post(
        "/api/v1/users/onboarding",
        json=onboarding_payload(),
    )

    assert create_response.status_code == 201

    response = await client.get("/api/v1/users/preferences")

    assert response.status_code == 200

    data = response.json()

    assert data["preferred_start_hour"] == 7
    assert data["preferred_end_hour"] == 10

    assert set(data["interests"]) == {
        "aqi",
        "uv",
        "rainfall",
        "visibility",
    }

    assert set(data["activity_contexts"]) == {
        "travel",
        "outdoor_health",
    }


@pytest.mark.asyncio
async def test_onboarding_cannot_be_completed_twice(
    client: AsyncClient,
):
    first_response = await client.post(
        "/api/v1/users/onboarding",
        json=onboarding_payload(),
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/users/onboarding",
        json=onboarding_payload(),
    )

    assert second_response.status_code == 409

    assert second_response.json()["detail"] == "Onboarding has already been completed"


@pytest.mark.asyncio
async def test_user_can_have_multiple_personas(
    client: AsyncClient,
):
    payload = onboarding_payload()

    payload["personas"] = [
        "farmer",
        "traveller",
        "health",
    ]

    response = await client.post(
        "/api/v1/users/onboarding",
        json=payload,
    )

    assert response.status_code == 201

    assert set(response.json()["personas"]) == {
        "farmer",
        "traveller",
        "health",
    }


@pytest.mark.asyncio
async def test_duplicate_personas_are_rejected(
    client: AsyncClient,
):
    payload = onboarding_payload()

    payload["personas"] = [
        "health",
        "health",
    ]

    response = await client.post(
        "/api/v1/users/onboarding",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_persona_is_rejected(
    client: AsyncClient,
):
    payload = onboarding_payload()

    payload["personas"] = ["fisherman"]

    response = await client.post(
        "/api/v1/users/onboarding",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_weather_interest_is_rejected(
    client: AsyncClient,
):
    payload = onboarding_payload()

    payload["interests"] = [
        "rainfall",
        "something_invalid",
    ]

    response = await client.post(
        "/api/v1/users/onboarding",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_activity_context_is_rejected(
    client: AsyncClient,
):
    payload = onboarding_payload()

    payload["activity_contexts"] = [
        "travel",
        "invalid_activity",
    ]

    response = await client.post(
        "/api/v1/users/onboarding",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_preferred_hour_is_rejected(
    client: AsyncClient,
):
    payload = onboarding_payload()

    payload["preferred_start_hour"] = 27

    response = await client.post(
        "/api/v1/users/onboarding",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_preserves_unrelated_preferences(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/users/onboarding",
        json=onboarding_payload(),
    )

    assert response.status_code == 201

    patch_response = await client.patch(
        "/api/v1/users/preferences",
        json={
            "preferred_start_hour": 6,
            "notifications": {
                "rain_alerts": False,
            },
        },
    )

    assert patch_response.status_code == 200

    data = patch_response.json()

    assert data["preferred_start_hour"] == 6
    assert data["notifications"]["rain_alerts"] is False

    # Unrelated values remain unchanged
    assert data["temperature_unit"] == "celsius"

    assert data["notifications"]["aqi_alerts"] is True

    assert data["notifications"]["daily_summary"] is True

    assert set(data["personas"]) == {
        "traveller",
        "health",
    }

    assert set(data["interests"]) == {
        "aqi",
        "uv",
        "rainfall",
        "visibility",
    }


@pytest.mark.asyncio
async def test_patch_can_replace_personas(
    client: AsyncClient,
):
    await client.post(
        "/api/v1/users/onboarding",
        json=onboarding_payload(),
    )

    response = await client.patch(
        "/api/v1/users/preferences",
        json={"personas": ["farmer"]},
    )

    assert response.status_code == 200

    assert response.json()["personas"] == ["farmer"]


@pytest.mark.asyncio
async def test_user_cannot_read_another_users_preferences(
    client: AsyncClient,
    second_user: User,
):
    response = await client.post(
        "/api/v1/users/onboarding",
        json=onboarding_payload(),
    )

    assert response.status_code == 201

    async def override_second_user():
        return second_user

    app.dependency_overrides[get_current_user] = override_second_user

    response = await client.get("/api/v1/users/preferences")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_onboarding_rolls_back_when_write_fails(
    session: AsyncSession,
    user: User,
):
    # Save the scalar value before rollback.
    # SQLAlchemy may expire ORM objects after rollback.
    user_id = user.id

    service = PreferenceService(session)

    payload = OnboardingRequest(**onboarding_payload())

    service.repository.replace_interests = AsyncMock(
        side_effect=RuntimeError("Simulated database failure")
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated database failure",
    ):
        await service.complete_onboarding(
            user_id,
            payload,
        )

    repository = PreferenceRepository(session)

    preference = await repository.get_preference(user_id)

    assert preference is None
