import uuid

import pytest
from httpx import AsyncClient

from app.dependencies.auth import get_current_user
from app.main import app
from app.models.user import User


def routine_payload(
    *,
    name: str = "Morning Run",
    saved_location_id: str | None = None,
) -> dict:
    return {
        "name": name,
        "activity_context": "outdoor_health",
        "saved_location_id": saved_location_id,
        "days_of_week": [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
        ],
        "start_time": "06:30:00",
        "duration_minutes": 60,
        "is_enabled": True,
    }


async def create_location(
    client: AsyncClient,
    *,
    label: str = "Home",
    city: str = "Delhi",
) -> dict:
    response = await client.post(
        "/api/v1/locations",
        json={
            "label": label,
            "city": city,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "location_type": "home",
            "is_primary": True,
        },
    )

    assert response.status_code == 201

    return response.json()


@pytest.mark.asyncio
async def test_user_can_create_routine_without_location(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/routines",
        json=routine_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Morning Run"
    assert data["activity_context"] == "outdoor_health"
    assert data["saved_location_id"] is None
    assert data["duration_minutes"] == 60
    assert data["is_enabled"] is True

    assert data["days_of_week"] == [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
    ]


@pytest.mark.asyncio
async def test_user_can_create_routine_with_saved_location(
    client: AsyncClient,
):
    location = await create_location(client)

    response = await client.post(
        "/api/v1/routines",
        json=routine_payload(saved_location_id=location["id"]),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["saved_location_id"] == location["id"]


@pytest.mark.asyncio
async def test_user_can_list_routines(
    client: AsyncClient,
):
    await client.post(
        "/api/v1/routines",
        json=routine_payload(name="Morning Run"),
    )

    await client.post(
        "/api/v1/routines",
        json={
            **routine_payload(name="Evening Walk"),
            "start_time": "18:00:00",
        },
    )

    response = await client.get("/api/v1/routines")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["name"] == "Morning Run"
    assert data[1]["name"] == "Evening Walk"


@pytest.mark.asyncio
async def test_user_can_update_routine(
    client: AsyncClient,
):
    create_response = await client.post(
        "/api/v1/routines",
        json=routine_payload(),
    )

    routine_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/routines/{routine_id}",
        json={
            "name": "Updated Morning Run",
            "duration_minutes": 90,
            "start_time": "07:00:00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Morning Run"

    assert data["duration_minutes"] == 90
    assert data["start_time"] == "07:00:00"


@pytest.mark.asyncio
async def test_patch_preserves_unrelated_fields(
    client: AsyncClient,
):
    create_response = await client.post(
        "/api/v1/routines",
        json=routine_payload(),
    )

    before = create_response.json()

    response = await client.patch(
        f"/api/v1/routines/{before['id']}",
        json={
            "name": "Renamed Routine",
        },
    )

    assert response.status_code == 200

    after = response.json()

    assert after["name"] == "Renamed Routine"

    assert after["activity_context"] == before["activity_context"]

    assert after["days_of_week"] == before["days_of_week"]

    assert after["duration_minutes"] == before["duration_minutes"]

    assert after["start_time"] == before["start_time"]


@pytest.mark.asyncio
async def test_user_can_clear_saved_location(
    client: AsyncClient,
):
    location = await create_location(client)

    create_response = await client.post(
        "/api/v1/routines",
        json=routine_payload(saved_location_id=location["id"]),
    )

    routine_id = create_response.json()["id"]

    assert create_response.json()["saved_location_id"] == location["id"]

    response = await client.patch(
        f"/api/v1/routines/{routine_id}",
        json={
            "saved_location_id": None,
        },
    )

    assert response.status_code == 200

    assert response.json()["saved_location_id"] is None


@pytest.mark.asyncio
async def test_user_can_disable_routine(
    client: AsyncClient,
):
    create_response = await client.post(
        "/api/v1/routines",
        json=routine_payload(),
    )

    routine_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/routines/{routine_id}",
        json={
            "is_enabled": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_enabled"] is False


@pytest.mark.asyncio
async def test_user_can_delete_routine(
    client: AsyncClient,
):
    create_response = await client.post(
        "/api/v1/routines",
        json=routine_payload(),
    )

    routine_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/routines/{routine_id}")

    assert response.status_code == 204

    list_response = await client.get("/api/v1/routines")

    assert list_response.status_code == 200
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_duplicate_weekdays_are_rejected(
    client: AsyncClient,
):
    payload = routine_payload()

    payload["days_of_week"] = [
        "monday",
        "monday",
    ]

    response = await client.post(
        "/api/v1/routines",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_weekday_is_rejected(
    client: AsyncClient,
):
    payload = routine_payload()

    payload["days_of_week"] = [
        "someday",
    ]

    response = await client.post(
        "/api/v1/routines",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_activity_context_is_rejected(
    client: AsyncClient,
):
    payload = routine_payload()

    payload["activity_context"] = "invalid_activity"

    response = await client.post(
        "/api/v1/routines",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_duration_below_minimum_is_rejected(
    client: AsyncClient,
):
    payload = routine_payload()

    payload["duration_minutes"] = 4

    response = await client.post(
        "/api/v1/routines",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_duration_above_maximum_is_rejected(
    client: AsyncClient,
):
    payload = routine_payload()

    payload["duration_minutes"] = 721

    response = await client.post(
        "/api/v1/routines",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_nonexistent_location_returns_404(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/routines",
        json=routine_payload(saved_location_id=str(uuid.uuid4())),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Saved location not found"


@pytest.mark.asyncio
async def test_cannot_use_another_users_location(
    client: AsyncClient,
    second_user: User,
):
    location = await create_location(client)

    async def override_second_user():
        return second_user

    app.dependency_overrides[get_current_user] = override_second_user

    try:
        response = await client.post(
            "/api/v1/routines",
            json=routine_payload(saved_location_id=(location["id"])),
        )

        assert response.status_code == 404

        assert response.json()["detail"] == "Saved location not found"

    finally:
        app.dependency_overrides.pop(
            get_current_user,
            None,
        )


@pytest.mark.asyncio
async def test_user_cannot_update_another_users_routine(
    client: AsyncClient,
    second_user: User,
):
    create_response = await client.post(
        "/api/v1/routines",
        json=routine_payload(),
    )

    routine_id = create_response.json()["id"]

    async def override_second_user():
        return second_user

    app.dependency_overrides[get_current_user] = override_second_user

    try:
        response = await client.patch(
            f"/api/v1/routines/{routine_id}",
            json={"name": "Hacked Routine"},
        )

        assert response.status_code == 404

        assert response.json()["detail"] == "Routine not found"

    finally:
        app.dependency_overrides.pop(
            get_current_user,
            None,
        )


@pytest.mark.asyncio
async def test_user_cannot_delete_another_users_routine(
    client: AsyncClient,
    second_user: User,
):
    create_response = await client.post(
        "/api/v1/routines",
        json=routine_payload(),
    )

    routine_id = create_response.json()["id"]

    async def override_second_user():
        return second_user

    app.dependency_overrides[get_current_user] = override_second_user

    try:
        response = await client.delete(f"/api/v1/routines/{routine_id}")

        assert response.status_code == 404

        assert response.json()["detail"] == "Routine not found"

    finally:
        app.dependency_overrides.pop(
            get_current_user,
            None,
        )
