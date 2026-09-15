from abc import ABC, abstractmethod
from typing import Any


class MarineProvider(ABC):
    @abstractmethod
    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        raise NotImplementedError