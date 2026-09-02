from app.core.enums import (
    PushRegistrationType,
)
from app.integrations.push.base import (
    PushMessage,
    PushProvider,
    PushSendResult,
)


class DisabledPushProvider(PushProvider):
    async def send(
        self,
        *,
        registration_id: str,
        registration_type: (PushRegistrationType),
        message: PushMessage,
    ) -> PushSendResult:
        return PushSendResult(message_id=None)
