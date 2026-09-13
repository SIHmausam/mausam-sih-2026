from abc import ABC, abstractmethod


class WeatherMapProviderError(RuntimeError):
    pass


class WeatherMapProvider(ABC):
    @abstractmethod
    async def get_tile(
        self,
        *,
        layer: str,
        zoom: int,
        x: int,
        y: int,
    ) -> bytes:
        raise NotImplementedError