import pytest
from httpx import AsyncClient

from app.core.redis import get_redis
from app.dependencies.providers import (
    get_alert_provider,
)
from app.integrations.alerts.base import (
    CapDocumentResult,
)
from app.main import app
from app.schemas.alert import (
    AlertArea,
    AlertCircle,
    AlertCoordinate,
    AlertPolygon,
    OfficialAlert,
)
from app.services.alert_service import (
    AlertCacheError,
    AlertService,
)

RSS_XML = """
<rss version="2.0">
    <channel>
        <title>CAP Integrated Alert System</title>

        <item>
            <title>
                Moderate Thunderstorm Warning
            </title>

            <description>
                Thunderstorm with rain and gusty wind
            </description>

            <link>
                https://sachet.ndma.gov.in/cap_public_website/
                FetchXMLFile?identifier=ALERT-001
            </link>

            <guid>
                ALERT-001
            </guid>

            <pubDate>
                Tue, 01 Sep 2026 01:20:52 GMT
            </pubDate>
        </item>
    </channel>
</rss>
"""


CAP_XML = """
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
    <identifier>ALERT-001</identifier>

    <sender>
        test@example.com
    </sender>

    <sent>
        2026-09-01T01:20:52+00:00
    </sent>

    <status>Actual</status>
    <msgType>Alert</msgType>
    <scope>Public</scope>

    <info>
        <language>en-IN</language>

        <category>Met</category>

        <event>
            Thunderstorm
        </event>

        <urgency>
            Immediate
        </urgency>

        <severity>
            Moderate
        </severity>

        <certainty>
            Likely
        </certainty>

        <effective>
            2026-09-01T01:20:52+00:00
        </effective>

        <onset>
            2026-09-01T01:30:00+00:00
        </onset>

        <expires>
            2026-09-01T04:30:00+00:00
        </expires>

        <senderName>
            India Meteorological Department
        </senderName>

        <headline>
            Moderate thunderstorm warning
        </headline>

        <description>
            Thunderstorm accompanied by rain
            and gusty winds.
        </description>

        <instruction>
            Stay indoors and avoid open areas.
        </instruction>

        <area>
            <areaDesc>
                Purulia, Birbhum and West Burdwan
            </areaDesc>
        </area>
    </info>
</alert>
"""


MULTILINGUAL_CAP_XML = """
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
    <identifier>
        ALERT-002
    </identifier>

    <info>
        <language>
            hi-IN
        </language>

        <event>
            आंधी
        </event>

        <headline>
            हिंदी चेतावनी
        </headline>

        <severity>
            Moderate
        </severity>
    </info>

    <info>
        <language>
            en-IN
        </language>

        <event>
            Thunderstorm
        </event>

        <headline>
            English warning
        </headline>

        <severity>
            Severe
        </severity>

        <area>
            <areaDesc>
                Delhi
            </areaDesc>
        </area>
    </info>
</alert>
"""


GEOMETRY_CAP_XML = """
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
    <identifier>
        GEO-001
    </identifier>

    <info>
        <language>
            en-IN
        </language>

        <event>
            Flood
        </event>

        <severity>
            Severe
        </severity>

        <area>
            <areaDesc>
                Delhi Region
            </areaDesc>

            <polygon>
                28.50,77.00
                28.80,77.00
                28.80,77.40
                28.50,77.40
            </polygon>

            <geocode>
                <valueName>
                    TEST_CODE
                </valueName>

                <value>
                    12345
                </value>
            </geocode>
        </area>

        <area>
            <areaDesc>
                Central Region
            </areaDesc>

            <circle>
                28.6139,77.2090 25
            </circle>
        </area>
    </info>
</alert>
"""


class FakeRedis:
    def __init__(self):
        self.storage: dict[
            str,
            str,
        ] = {}

    async def get(
        self,
        key: str,
    ) -> str | None:
        return self.storage.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
    ):
        self.storage[key] = value


class FakeAlertProvider:
    def __init__(self):
        self.feed_calls = 0
        self.cap_calls = 0

        self.last_identifier: str | None = None

        self.last_etag: str | None = None

        self.return_not_modified = False

    async def get_feed(
        self,
    ) -> str:
        self.feed_calls += 1

        return RSS_XML

    async def get_cap_document(
        self,
        identifier: str,
        etag: str | None = None,
    ) -> CapDocumentResult:
        self.cap_calls += 1

        self.last_identifier = identifier

        self.last_etag = etag

        if self.return_not_modified:
            return CapDocumentResult(
                content=None,
                etag=etag,
                not_modified=True,
            )

        return CapDocumentResult(
            content=CAP_XML,
            etag='"etag-v1"',
            not_modified=False,
        )


@pytest.mark.asyncio
async def test_alert_feed_is_normalized():
    provider = FakeAlertProvider()
    redis = FakeRedis()

    service = AlertService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_feed()

    assert len(response.alerts) == 1

    alert = response.alerts[0]

    assert alert.identifier == "ALERT-001"

    assert alert.title == "Moderate Thunderstorm Warning"

    assert alert.description == ("Thunderstorm with rain and gusty wind")

    assert alert.published_at is not None

    assert provider.feed_calls == 1


@pytest.mark.asyncio
async def test_cap_alert_is_normalized():
    provider = FakeAlertProvider()
    redis = FakeRedis()

    service = AlertService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_alert(
        identifier="ALERT-001",
    )

    assert response.identifier == "ALERT-001"

    assert response.event == "Thunderstorm"

    assert response.headline == ("Moderate thunderstorm warning")

    assert response.description == ("Thunderstorm accompanied by rain and gusty winds.")

    assert response.instruction == ("Stay indoors and avoid open areas.")

    assert response.severity == "Moderate"

    assert response.urgency == "Immediate"

    assert response.certainty == "Likely"

    assert response.effective_at is not None

    assert response.onset_at is not None

    assert response.expires_at is not None

    assert response.area_description == ("Purulia, Birbhum and West Burdwan")

    assert response.sender_name == ("India Meteorological Department")


def test_cap_parser_prefers_english_info():
    response = AlertService._parse_cap(MULTILINGUAL_CAP_XML)

    assert response.identifier == "ALERT-002"

    assert response.event == "Thunderstorm"

    assert response.headline == "English warning"

    assert response.severity == "Severe"

    assert response.area_description == "Delhi"


def test_cap_parser_extracts_geometry():
    response = AlertService._parse_cap(GEOMETRY_CAP_XML)

    assert response.identifier == "GEO-001"

    assert len(response.areas) == 2

    first_area = response.areas[0]

    assert first_area.description == "Delhi Region"

    assert len(first_area.polygons) == 1

    polygon = first_area.polygons[0]

    assert len(polygon.points) == 4

    assert polygon.points[0].latitude == 28.5

    assert polygon.points[0].longitude == 77.0

    assert len(first_area.geocodes) == 1

    assert first_area.geocodes[0].value_name == "TEST_CODE"

    assert first_area.geocodes[0].value == "12345"

    second_area = response.areas[1]

    assert len(second_area.circles) == 1

    circle = second_area.circles[0]

    assert circle.center.latitude == 28.6139

    assert circle.center.longitude == 77.2090

    assert circle.radius_km == 25


@pytest.mark.asyncio
async def test_first_cap_request_stores_cache():
    provider = FakeAlertProvider()
    redis = FakeRedis()

    service = AlertService(
        provider=provider,
        redis=redis,
    )

    await service.get_alert(
        identifier="ALERT-001",
    )

    xml_key = "alerts:cap:ALERT-001:xml"

    etag_key = "alerts:cap:ALERT-001:etag"

    fresh_key = "alerts:cap:ALERT-001:fresh"

    assert xml_key in redis.storage

    assert etag_key in redis.storage

    assert fresh_key in redis.storage

    assert redis.storage[xml_key] == CAP_XML

    assert redis.storage[etag_key] == '"etag-v1"'

    assert redis.storage[fresh_key] == "1"

    assert provider.cap_calls == 1
    assert provider.last_etag is None


@pytest.mark.asyncio
async def test_second_cap_request_uses_fresh_cache():
    provider = FakeAlertProvider()
    redis = FakeRedis()

    service = AlertService(
        provider=provider,
        redis=redis,
    )

    first = await service.get_alert(
        identifier="ALERT-001",
    )

    second = await service.get_alert(
        identifier="ALERT-001",
    )

    assert first == second

    # Second request must not contact
    # SACHET while cache is fresh.
    assert provider.cap_calls == 1


@pytest.mark.asyncio
async def test_stale_cache_revalidates_with_etag():
    provider = FakeAlertProvider()
    redis = FakeRedis()

    service = AlertService(
        provider=provider,
        redis=redis,
    )

    await service.get_alert(
        identifier="ALERT-001",
    )

    redis.storage.pop(
        ("alerts:cap:ALERT-001:fresh"),
        None,
    )

    provider.return_not_modified = True

    response = await service.get_alert(
        identifier="ALERT-001",
    )

    assert response.identifier == "ALERT-001"

    assert provider.last_etag == '"etag-v1"'

    assert provider.cap_calls == 2


@pytest.mark.asyncio
async def test_304_uses_cached_xml():
    provider = FakeAlertProvider()
    redis = FakeRedis()

    redis.storage[("alerts:cap:ALERT-001:xml")] = CAP_XML

    redis.storage[("alerts:cap:ALERT-001:etag")] = '"etag-v1"'

    provider.return_not_modified = True

    service = AlertService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_alert(
        identifier="ALERT-001",
    )

    assert response.identifier == "ALERT-001"

    assert response.event == "Thunderstorm"

    assert provider.last_etag == '"etag-v1"'

    assert redis.storage[("alerts:cap:ALERT-001:fresh")] == "1"


@pytest.mark.asyncio
async def test_304_without_cached_xml_raises_error():
    provider = FakeAlertProvider()
    redis = FakeRedis()

    redis.storage[("alerts:cap:ALERT-001:etag")] = '"etag-v1"'

    provider.return_not_modified = True

    service = AlertService(
        provider=provider,
        redis=redis,
    )

    with pytest.raises(
        AlertCacheError,
        match=("CAP XML cache missing"),
    ):
        await service.get_alert(
            identifier="ALERT-001",
        )


def test_point_inside_alert_polygon():
    alert = OfficialAlert(
        identifier="POLYGON-001",
        areas=[
            AlertArea(
                description="Delhi",
                polygons=[
                    AlertPolygon(
                        points=[
                            AlertCoordinate(
                                latitude=28.5,
                                longitude=77.0,
                            ),
                            AlertCoordinate(
                                latitude=28.8,
                                longitude=77.0,
                            ),
                            AlertCoordinate(
                                latitude=28.8,
                                longitude=77.4,
                            ),
                            AlertCoordinate(
                                latitude=28.5,
                                longitude=77.4,
                            ),
                        ]
                    )
                ],
            )
        ],
    )

    assert AlertService.is_alert_relevant(
        alert=alert,
        latitude=28.6139,
        longitude=77.2090,
    )


def test_point_outside_alert_polygon():
    alert = OfficialAlert(
        identifier="POLYGON-002",
        areas=[
            AlertArea(
                polygons=[
                    AlertPolygon(
                        points=[
                            AlertCoordinate(
                                latitude=28.5,
                                longitude=77.0,
                            ),
                            AlertCoordinate(
                                latitude=28.8,
                                longitude=77.0,
                            ),
                            AlertCoordinate(
                                latitude=28.8,
                                longitude=77.4,
                            ),
                            AlertCoordinate(
                                latitude=28.5,
                                longitude=77.4,
                            ),
                        ]
                    )
                ]
            )
        ],
    )

    assert not (
        AlertService.is_alert_relevant(
            alert=alert,
            latitude=30.3165,
            longitude=78.0322,
        )
    )


def test_point_inside_alert_circle():
    alert = OfficialAlert(
        identifier="CIRCLE-001",
        areas=[
            AlertArea(
                circles=[
                    AlertCircle(
                        center=(
                            AlertCoordinate(
                                latitude=28.6139,
                                longitude=77.2090,
                            )
                        ),
                        radius_km=25,
                    )
                ]
            )
        ],
    )

    assert AlertService.is_alert_relevant(
        alert=alert,
        latitude=28.6200,
        longitude=77.2100,
    )


def test_point_outside_alert_circle():
    alert = OfficialAlert(
        identifier="CIRCLE-002",
        areas=[
            AlertArea(
                circles=[
                    AlertCircle(
                        center=(
                            AlertCoordinate(
                                latitude=28.6139,
                                longitude=77.2090,
                            )
                        ),
                        radius_km=5,
                    )
                ]
            )
        ],
    )

    assert not (
        AlertService.is_alert_relevant(
            alert=alert,
            latitude=30.3165,
            longitude=78.0322,
        )
    )


def test_city_fallback_when_geometry_missing():
    alert = OfficialAlert(
        identifier="CITY-001",
        areas=[AlertArea(description=("Delhi, New Delhi and surrounding areas"))],
    )

    assert AlertService.is_alert_relevant(
        alert=alert,
        latitude=28.6139,
        longitude=77.2090,
        city="Delhi",
    )


def test_city_matching_is_case_insensitive():
    alert = OfficialAlert(
        identifier="CITY-002",
        areas=[AlertArea(description=("DELHI AND SURROUNDING AREAS"))],
    )

    assert AlertService.is_alert_relevant(
        alert=alert,
        latitude=28.6139,
        longitude=77.2090,
        city="delhi",
    )


def test_city_fallback_not_used_when_geometry_exists():
    alert = OfficialAlert(
        identifier=("GEOMETRY-001"),
        areas=[
            AlertArea(
                description="Delhi",
                polygons=[
                    AlertPolygon(
                        points=[
                            AlertCoordinate(
                                latitude=20.0,
                                longitude=70.0,
                            ),
                            AlertCoordinate(
                                latitude=21.0,
                                longitude=70.0,
                            ),
                            AlertCoordinate(
                                latitude=21.0,
                                longitude=71.0,
                            ),
                            AlertCoordinate(
                                latitude=20.0,
                                longitude=71.0,
                            ),
                        ]
                    )
                ],
            )
        ],
    )

    assert not (
        AlertService.is_alert_relevant(
            alert=alert,
            latitude=28.6139,
            longitude=77.2090,
            city="Delhi",
        )
    )


@pytest.mark.asyncio
async def test_relevant_alerts_returns_matching_alert():
    provider = FakeAlertProvider()
    redis = FakeRedis()

    service = AlertService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_relevant_alerts(
        latitude=28.6139,
        longitude=77.2090,
        city="Purulia",
    )

    assert len(response) == 1

    assert response[0].identifier == "ALERT-001"


@pytest.mark.asyncio
async def test_relevant_alerts_returns_empty_when_not_matching():
    provider = FakeAlertProvider()
    redis = FakeRedis()

    service = AlertService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_relevant_alerts(
        latitude=30.3165,
        longitude=78.0322,
        city="Dehradun",
    )

    assert response == []


@pytest.mark.asyncio
async def test_alert_feed_endpoint(
    client: AsyncClient,
):
    provider = FakeAlertProvider()
    redis = FakeRedis()

    def override_provider():
        return provider

    async def override_redis():
        return redis

    app.dependency_overrides[get_alert_provider] = override_provider

    app.dependency_overrides[get_redis] = override_redis

    try:
        response = await client.get("/api/v1/alerts")

        assert response.status_code == 200

        data = response.json()

        assert len(data["alerts"]) == 1

        assert data["alerts"][0]["identifier"] == "ALERT-001"

    finally:
        app.dependency_overrides.pop(
            get_alert_provider,
            None,
        )

        app.dependency_overrides.pop(
            get_redis,
            None,
        )


@pytest.mark.asyncio
async def test_alert_detail_endpoint(
    client: AsyncClient,
):
    provider = FakeAlertProvider()
    redis = FakeRedis()

    def override_provider():
        return provider

    async def override_redis():
        return redis

    app.dependency_overrides[get_alert_provider] = override_provider

    app.dependency_overrides[get_redis] = override_redis

    try:
        response = await client.get("/api/v1/alerts/ALERT-001")

        assert response.status_code == 200

        data = response.json()

        assert data["identifier"] == "ALERT-001"

        assert data["event"] == "Thunderstorm"

        assert data["severity"] == "Moderate"

        assert data["area_description"] == ("Purulia, Birbhum and West Burdwan")

    finally:
        app.dependency_overrides.pop(
            get_alert_provider,
            None,
        )

        app.dependency_overrides.pop(
            get_redis,
            None,
        )
