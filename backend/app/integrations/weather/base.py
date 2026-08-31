from abc import ABC, abstractmethod
from typing import Any


class WeatherProvider(ABC):
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

    @abstractmethod
    async def get_daily(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_agriculture_context(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        raise NotImplementedError
