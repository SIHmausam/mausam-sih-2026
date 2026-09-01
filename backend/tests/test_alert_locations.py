
from app.schemas.alert import OfficialAlert


class FakeAlertService:
    def __init__(self):
        self.calls = 0

        self.latitude: float | None = None
        self.longitude: float | None = None
        self.city: str | None = None

    async def get_relevant_alerts(
        self,
        latitude: float,
        longitude: float,
        city: str | None = None,
    ) -> list[OfficialAlert]:
        self.calls += 1

        self.latitude = latitude
        self.longitude = longitude
        self.city = city

        return [
            OfficialAlert(
                identifier="TEST-ALERT-001",
                event="Thunderstorm",
                severity="Severe",
                area_description=city,
            )
        ]
