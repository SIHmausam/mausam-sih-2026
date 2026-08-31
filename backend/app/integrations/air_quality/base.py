from abc import ABC, abstractmethod
from typing import Any


class AirQualityProvider(ABC):
    @abstractmethod
    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_hourly(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        raise NotImplementedError
