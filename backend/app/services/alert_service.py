import asyncio
import math
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlparse
from xml.etree.ElementTree import Element

from defusedxml import ElementTree
from pydantic import TypeAdapter
from redis.asyncio import Redis

from app.integrations.alerts.base import AlertProvider
from app.schemas.alert import (
    AlertArea,
    AlertCircle,
    AlertCoordinate,
    AlertFeedItem,
    AlertFeedResponse,
    AlertGeocode,
    AlertPolygon,
    OfficialAlert,
)


class AlertCacheError(Exception):
    pass


official_alert_snapshot_adapter = TypeAdapter(dict[str, OfficialAlert])


class AlertService:
    # Keep CAP XML and ETag available for recovery/revalidation.
    CAP_CACHE_TTL = 21600  # 6 hours

    # During this period, serve cached XML without contacting SACHET.
    CAP_REVALIDATE_TTL = 120  # 2 minutes

    # Avoid sending a large burst of requests to SACHET.
    MAX_CAP_CONCURRENCY = 3
    FEED_CACHE_TTL = 60

    SNAPSHOT_KEY = "alerts:snapshot:official"

    SNAPSHOT_REFRESHED_AT_KEY = "alerts:snapshot:refreshed_at"

    def __init__(
        self,
        provider: AlertProvider,
        redis: Redis,
    ):
        self.provider = provider
        self.redis = redis

    async def get_cached_alert_snapshot(
        self,
    ) -> dict[str, OfficialAlert]:
        cached = await self.redis.get(self.SNAPSHOT_KEY)

        if cached is None:
            return {}

        try:
            return official_alert_snapshot_adapter.validate_json(cached)

        except ValueError:
            return {}

    async def refresh_alert_snapshot(
        self,
    ) -> list[OfficialAlert]:
        feed = await self.get_feed()

        existing_snapshot = await self.get_cached_alert_snapshot()

        feed_identifiers = list(
            dict.fromkeys(
                item.identifier for item in feed.alerts if item.identifier is not None
            )
        )

        semaphore = asyncio.Semaphore(self.MAX_CAP_CONCURRENCY)

        async def fetch_alert(
            feed_identifier: str,
        ) -> tuple[
            str,
            OfficialAlert | None,
        ]:
            existing_alert = existing_snapshot.get(feed_identifier)

            # Alert already exists in the latest
            # normalized snapshot.
            if existing_alert is not None:
                return (
                    feed_identifier,
                    existing_alert,
                )

            async with semaphore:
                try:
                    alert = await self.get_alert(feed_identifier)

                except (
                    AlertCacheError,
                    ValueError,
                ):
                    return (
                        feed_identifier,
                        None,
                    )

            return (
                feed_identifier,
                alert,
            )

        results = await asyncio.gather(
            *[fetch_alert(identifier) for identifier in feed_identifiers]
        )

        # Only alerts still present in the current
        # RSS feed remain in the snapshot.
        snapshot = {
            feed_identifier: alert
            for (
                feed_identifier,
                alert,
            ) in results
            if alert is not None
        }

        await self.redis.set(
            self.SNAPSHOT_KEY,
            official_alert_snapshot_adapter.dump_json(snapshot),
        )

        await self.redis.set(
            self.SNAPSHOT_REFRESHED_AT_KEY,
            datetime.now(UTC).isoformat(),
        )

        return list(snapshot.values())

    @staticmethod
    def _text(
        element: Element,
        tag: str,
    ) -> str | None:
        child = element.find(tag)

        if child is None or child.text is None:
            return None

        value = " ".join(child.text.split())

        return value or None

    @staticmethod
    def _local_name(
        tag: str,
    ) -> str:
        if "}" in tag:
            return tag.split(
                "}",
                1,
            )[1]

        return tag

    @classmethod
    def _child(
        cls,
        element: Element,
        name: str,
    ) -> Element | None:
        for child in element:
            if cls._local_name(child.tag) == name:
                return child

        return None

    @classmethod
    def _children(
        cls,
        element: Element,
        name: str,
    ) -> list[Element]:
        return [child for child in element if (cls._local_name(child.tag) == name)]

    @classmethod
    def _child_text(
        cls,
        element: Element | None,
        name: str,
    ) -> str | None:
        if element is None:
            return None

        child = cls._child(
            element,
            name,
        )

        if child is None or child.text is None:
            return None

        value = " ".join(child.text.split())

        return value or None

    @staticmethod
    def _normalize_datetime(
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

    @classmethod
    def _is_active_alert(
        cls,
        alert: OfficialAlert,
        now: datetime,
    ) -> bool:
        start = alert.onset_at or alert.effective_at

        if start is not None:
            normalized_start = cls._normalize_datetime(start)

            if normalized_start > now:
                return False

        if alert.expires_at is not None:
            normalized_expiry = cls._normalize_datetime(alert.expires_at)

            if normalized_expiry < now:
                return False

        return True

    @staticmethod
    def _decode_redis_value(
        value: str | bytes | None,
    ) -> str | None:
        if value is None:
            return None

        if isinstance(
            value,
            bytes,
        ):
            return value.decode("utf-8")

        return value

    @staticmethod
    def _parse_datetime(
        value: str | None,
    ) -> datetime | None:
        if value is None:
            return None

        try:
            return datetime.fromisoformat(value)

        except ValueError:
            return None

    @staticmethod
    def _extract_identifier(
        link: str | None,
        guid: str | None,
    ) -> str | None:
        for value in (
            link,
            guid,
        ):
            if not value:
                continue

            parsed = urlparse(value)

            identifier = parse_qs(parsed.query).get("identifier")

            if identifier:
                return identifier[0]

        if guid and "://" not in guid:
            return guid.strip()

        return None

    async def get_feed(
        self,
    ) -> AlertFeedResponse:
        cache_key = "alerts:rss:feed"

        cached = await self.redis.get(cache_key)

        if cached:
            return AlertFeedResponse.model_validate_json(cached)

        xml = await self.provider.get_feed()

        root = ElementTree.fromstring(xml)

        items: list[AlertFeedItem] = []

        for item in root.findall(".//item"):
            title = (
                self._text(
                    item,
                    "title",
                )
                or "Official Alert"
            )

            description = self._text(
                item,
                "description",
            )

            link = self._text(
                item,
                "link",
            )

            guid = self._text(
                item,
                "guid",
            )

            pub_date = self._text(
                item,
                "pubDate",
            )

            published_at = None

            if pub_date:
                try:
                    published_at = parsedate_to_datetime(pub_date)

                except (
                    TypeError,
                    ValueError,
                    OverflowError,
                ):
                    published_at = None

            items.append(
                AlertFeedItem(
                    identifier=(
                        self._extract_identifier(
                            link,
                            guid,
                        )
                    ),
                    title=title,
                    description=description,
                    link=link,
                    published_at=published_at,
                )
            )

        response = AlertFeedResponse(alerts=items)

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=self.FEED_CACHE_TTL,
        )

        return response

    @classmethod
    def _select_info(
        cls,
        root: Element,
    ) -> Element | None:
        info_elements = cls._children(
            root,
            "info",
        )

        if not info_elements:
            return None

        # Prefer English CAP content.
        for info in info_elements:
            language = cls._child_text(
                info,
                "language",
            )

            if language and language.lower().startswith("en"):
                return info

        return info_elements[0]

    @staticmethod
    def _parse_polygon(
        value: str | None,
    ) -> AlertPolygon | None:
        if not value:
            return None

        points: list[AlertCoordinate] = []

        for pair in value.split():
            try:
                (
                    latitude_text,
                    longitude_text,
                ) = pair.split(
                    ",",
                    1,
                )

                latitude = float(latitude_text)

                longitude = float(longitude_text)

            except (
                ValueError,
                TypeError,
            ):
                continue

            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                continue

            points.append(
                AlertCoordinate(
                    latitude=latitude,
                    longitude=longitude,
                )
            )

        if len(points) < 3:
            return None

        return AlertPolygon(points=points)

    @staticmethod
    def _parse_circle(
        value: str | None,
    ) -> AlertCircle | None:
        if not value:
            return None

        parts = value.split()

        if len(parts) != 2:
            return None

        coordinates_text = parts[0]
        radius_text = parts[1]

        try:
            (
                latitude_text,
                longitude_text,
            ) = coordinates_text.split(
                ",",
                1,
            )

            latitude = float(latitude_text)

            longitude = float(longitude_text)

            radius_km = float(radius_text)

        except (
            ValueError,
            TypeError,
        ):
            return None

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180 and radius_km >= 0):
            return None

        return AlertCircle(
            center=AlertCoordinate(
                latitude=latitude,
                longitude=longitude,
            ),
            radius_km=radius_km,
        )

    @classmethod
    def _parse_geocode(
        cls,
        element: Element,
    ) -> AlertGeocode | None:
        value_name = cls._child_text(
            element,
            "valueName",
        )

        value = cls._child_text(
            element,
            "value",
        )

        if not value_name or not value:
            return None

        return AlertGeocode(
            value_name=value_name,
            value=value,
        )

    @classmethod
    def _parse_area(
        cls,
        area: Element,
    ) -> AlertArea:
        description = cls._child_text(
            area,
            "areaDesc",
        )

        polygons: list[AlertPolygon] = []

        for polygon_element in cls._children(
            area,
            "polygon",
        ):
            polygon = cls._parse_polygon(polygon_element.text)

            if polygon is not None:
                polygons.append(polygon)

        circles: list[AlertCircle] = []

        for circle_element in cls._children(
            area,
            "circle",
        ):
            circle = cls._parse_circle(circle_element.text)

            if circle is not None:
                circles.append(circle)

        geocodes: list[AlertGeocode] = []

        for geocode_element in cls._children(
            area,
            "geocode",
        ):
            geocode = cls._parse_geocode(geocode_element)

            if geocode is not None:
                geocodes.append(geocode)

        return AlertArea(
            description=description,
            polygons=polygons,
            circles=circles,
            geocodes=geocodes,
        )

    @classmethod
    def _parse_cap(
        cls,
        xml: str,
    ) -> OfficialAlert:
        root = ElementTree.fromstring(xml)

        identifier = cls._child_text(
            root,
            "identifier",
        )

        if not identifier:
            raise ValueError("CAP alert does not contain an identifier")

        info = cls._select_info(root)

        event = cls._child_text(
            info,
            "event",
        )

        headline = cls._child_text(
            info,
            "headline",
        )

        description = cls._child_text(
            info,
            "description",
        )

        instruction = cls._child_text(
            info,
            "instruction",
        )

        severity = cls._child_text(
            info,
            "severity",
        )

        urgency = cls._child_text(
            info,
            "urgency",
        )

        certainty = cls._child_text(
            info,
            "certainty",
        )

        effective = cls._child_text(
            info,
            "effective",
        )

        onset = cls._child_text(
            info,
            "onset",
        )

        expires = cls._child_text(
            info,
            "expires",
        )

        sender_name = cls._child_text(
            info,
            "senderName",
        )

        areas: list[AlertArea] = []

        area_descriptions: list[str] = []

        if info is not None:
            for area_element in cls._children(
                info,
                "area",
            ):
                area = cls._parse_area(area_element)

                areas.append(area)

                if area.description:
                    area_descriptions.append(area.description)

        return OfficialAlert(
            identifier=identifier,
            event=event,
            headline=headline,
            description=description,
            instruction=instruction,
            severity=severity,
            urgency=urgency,
            certainty=certainty,
            effective_at=(cls._parse_datetime(effective)),
            onset_at=(cls._parse_datetime(onset)),
            expires_at=(cls._parse_datetime(expires)),
            area_description=(
                "; ".join(area_descriptions) if area_descriptions else None
            ),
            areas=areas,
            sender_name=sender_name,
        )

    async def get_alert(
        self,
        identifier: str,
    ) -> OfficialAlert:
        xml_key = f"alerts:cap:{identifier}:xml"

        etag_key = f"alerts:cap:{identifier}:etag"

        fresh_key = f"alerts:cap:{identifier}:fresh"

        cached_xml = self._decode_redis_value(await self.redis.get(xml_key))

        cache_is_fresh = await self.redis.get(fresh_key) is not None

        # Fast path:
        # no network request when the CAP document
        # was recently validated.
        if cached_xml is not None and cache_is_fresh:
            return self._parse_cap(cached_xml)

        cached_etag = self._decode_redis_value(await self.redis.get(etag_key))

        result = await self.provider.get_cap_document(
            identifier=identifier,
            etag=cached_etag,
        )

        # SACHET returned 304:
        # use already cached XML.
        if result.not_modified:
            if cached_xml is None:
                raise AlertCacheError("CAP XML cache missing for unchanged alert")

            await self.redis.set(
                fresh_key,
                "1",
                ex=self.CAP_REVALIDATE_TTL,
            )

            return self._parse_cap(cached_xml)

        if result.content is None:
            raise AlertCacheError("CAP provider returned no XML")

        # New/updated CAP document.
        await self.redis.set(
            xml_key,
            result.content,
            ex=self.CAP_CACHE_TTL,
        )

        if result.etag is not None:
            await self.redis.set(
                etag_key,
                result.etag,
                ex=self.CAP_CACHE_TTL,
            )

        await self.redis.set(
            fresh_key,
            "1",
            ex=self.CAP_REVALIDATE_TTL,
        )

        return self._parse_cap(result.content)

    @staticmethod
    def _point_in_polygon(
        latitude: float,
        longitude: float,
        polygon: AlertPolygon,
    ) -> bool:
        points = polygon.points

        inside = False

        j = len(points) - 1

        for i in range(len(points)):
            lat_i = points[i].latitude

            lon_i = points[i].longitude

            lat_j = points[j].latitude

            lon_j = points[j].longitude

            intersects = ((lat_i > latitude) != (lat_j > latitude)) and (
                longitude
                < (
                    (lon_j - lon_i)
                    * (latitude - lat_i)
                    / (lat_j - lat_i if lat_j != lat_i else 1e-12)
                    + lon_i
                )
            )

            if intersects:
                inside = not inside

            j = i

        return inside

    @staticmethod
    def _distance_km(
        latitude_a: float,
        longitude_a: float,
        latitude_b: float,
        longitude_b: float,
    ) -> float:
        earth_radius_km = 6371.0088

        lat1 = math.radians(latitude_a)

        lat2 = math.radians(latitude_b)

        delta_lat = math.radians(latitude_b - latitude_a)

        delta_lon = math.radians(longitude_b - longitude_a)

        haversine = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        )

        return 2 * earth_radius_km * math.asin(math.sqrt(haversine))

    @classmethod
    def _point_in_circle(
        cls,
        latitude: float,
        longitude: float,
        circle: AlertCircle,
    ) -> bool:
        distance = cls._distance_km(
            latitude,
            longitude,
            circle.center.latitude,
            circle.center.longitude,
        )

        return distance <= circle.radius_km

    @classmethod
    def is_alert_relevant(
        cls,
        alert: OfficialAlert,
        latitude: float,
        longitude: float,
        city: str | None = None,
    ) -> bool:
        for area in alert.areas:
            for polygon in area.polygons:
                if cls._point_in_polygon(
                    latitude,
                    longitude,
                    polygon,
                ):
                    return True

            for circle in area.circles:
                if cls._point_in_circle(
                    latitude,
                    longitude,
                    circle,
                ):
                    return True

        has_geometry = any(area.polygons or area.circles for area in alert.areas)

        # areaDesc fallback is only used when CAP
        # does not provide usable geometry.
        if not has_geometry and city:
            normalized_city = city.strip().casefold()

            for area in alert.areas:
                if not (area.description):
                    continue

                if normalized_city in (area.description.casefold()):
                    return True

        return False

    async def get_relevant_alerts(
        self,
        latitude: float,
        longitude: float,
        city: str | None = None,
    ) -> list[OfficialAlert]:
        """
        Return active official alerts relevant
        to a location using the latest Redis
        snapshot.

        This method performs no SACHET network
        requests.
        """

        snapshot = await self.get_cached_alert_snapshot()

        alerts = list(snapshot.values())

        now = datetime.now(UTC)

        return [
            alert
            for alert in alerts
            if (
                self._is_active_alert(
                    alert,
                    now,
                )
                and self.is_alert_relevant(
                    alert=alert,
                    latitude=latitude,
                    longitude=longitude,
                    city=city,
                )
            )
        ]
