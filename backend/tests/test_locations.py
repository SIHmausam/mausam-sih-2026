import pytest
from httpx import AsyncClient

from app.dependencies.auth import get_current_user
from app.main import app
from app.models.user import User


def location_payload(
    label: str = "Home",
    *,
    city: str = "Dehradun",
    is_primary: bool = True,
) -> dict:
    return {
        "label": label,
        "city": city,
        "latitude": 30.3165,
        "longitude": 78.0322,
        "location_type": "home",
        "is_primary": is_primary,
    }


@pytest.mark.asyncio
async def test_user_can_create_location(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/locations",
        json=location_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["label"] == "Home"
    assert data["city"] == "Dehradun"
    assert data["latitude"] == 30.3165
    assert data["longitude"] == 78.0322
    assert data["location_type"] == "home"
    assert data["is_primary"] is True


@pytest.mark.asyncio
async def test_city_is_required(
    client: AsyncClient,
):
    payload = location_payload()

    payload.pop("city")

    response = await client.post(
        "/api/v1/locations",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_user_can_list_locations(
    client: AsyncClient,
):
    await client.post(
        "/api/v1/locations",
        json=location_payload(),
    )

    response = await client.get("/api/v1/locations")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["city"] == "Dehradun"


@pytest.mark.asyncio
async def test_invalid_latitude_is_rejected(
    client: AsyncClient,
):
    payload = location_payload()

    payload["latitude"] = 91

    response = await client.post(
        "/api/v1/locations",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_longitude_is_rejected(
    client: AsyncClient,
):
    payload = location_payload()

    payload["longitude"] = 181

    response = await client.post(
        "/api/v1/locations",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_user_can_update_location(
    client: AsyncClient,
):
    create_response = await client.post(
        "/api/v1/locations",
        json=location_payload(),
    )

    location_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/locations/{location_id}",
        json={
            "label": "Delhi Home",
            "city": "Delhi",
            "location_type": "work",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["label"] == "Delhi Home"
    assert data["city"] == "Delhi"
    assert data["location_type"] == "work"


@pytest.mark.asyncio
async def test_only_one_location_is_primary(
    client: AsyncClient,
):
    first_response = await client.post(
        "/api/v1/locations",
        json=location_payload(
            label="Home",
            city="Dehradun",
            is_primary=True,
        ),
    )

    assert first_response.status_code == 201

    second_payload = {
        "label": "Farm",
        "city": "Haridwar",
        "latitude": 30.4,
        "longitude": 78.1,
        "location_type": "farm",
        "is_primary": True,
    }

    second_response = await client.post(
        "/api/v1/locations",
        json=second_payload,
    )

    assert second_response.status_code == 201

    response = await client.get("/api/v1/locations")

    locations = response.json()

    primary_locations = [location for location in locations if location["is_primary"]]

    assert len(primary_locations) == 1
    assert primary_locations[0]["label"] == "Farm"


@pytest.mark.asyncio
async def test_user_can_delete_location(
    client: AsyncClient,
):
    create_response = await client.post(
        "/api/v1/locations",
        json=location_payload(),
    )

    location_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/locations/{location_id}")

    assert response.status_code == 204

    list_response = await client.get("/api/v1/locations")

    assert list_response.json() == []


@pytest.mark.asyncio
async def test_user_cannot_update_another_users_location(
    client: AsyncClient,
    second_user: User,
):
    create_response = await client.post(
        "/api/v1/locations",
        json=location_payload(),
    )

    location_id = create_response.json()["id"]

    async def override_second_user():
        return second_user

    app.dependency_overrides[get_current_user] = override_second_user

    response = await client.patch(
        f"/api/v1/locations/{location_id}",
        json={
            "label": "Hacked Location",
            "city": "Mumbai",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_cannot_delete_another_users_location(
    client: AsyncClient,
    second_user: User,
):
    create_response = await client.post(
        "/api/v1/locations",
        json=location_payload(),
    )

    location_id = create_response.json()["id"]

    async def override_second_user():
        return second_user

    app.dependency_overrides[get_current_user] = override_second_user

    response = await client.delete(f"/api/v1/locations/{location_id}")

    assert response.status_code == 404
