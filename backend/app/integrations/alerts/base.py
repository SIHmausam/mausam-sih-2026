from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CapDocumentResult:
    content: str | None
    etag: str | None
    not_modified: bool = False


class AlertProvider(ABC):
    @abstractmethod
    async def get_feed(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_cap_document(
        self,
        identifier: str,
        etag: str | None = None,
    ) -> CapDocumentResult:
        raise NotImplementedError
