from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass

from app.core.enums import (
    PushRegistrationType,
)


@dataclass(frozen=True)
class PushMessage:
    title: str
    body: str
    data: dict[str, str]


@dataclass(frozen=True)
class PushSendResult:
    message_id: str | None


class PushProviderError(Exception):
    pass


class InvalidPushRegistrationError(PushProviderError):
    """
    The FID/token is no longer valid.

    The backend should deactivate the
    corresponding device registration.
    """


class TemporaryPushProviderError(PushProviderError):
    """
    Temporary provider failure.

    Later this can be retried by a worker.
    """


class PushProvider(ABC):
    @abstractmethod
    async def send(
        self,
        *,
        registration_id: str,
        registration_type: (PushRegistrationType),
        message: PushMessage,
    ) -> PushSendResult:
        raise NotImplementedError
