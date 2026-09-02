import asyncio

import firebase_admin
from firebase_admin import (
    credentials,
    exceptions,
    messaging,
)

from app.core.enums import (
    PushRegistrationType,
)
from app.integrations.push.base import (
    InvalidPushRegistrationError,
    PushMessage,
    PushProvider,
    PushProviderError,
    PushSendResult,
    TemporaryPushProviderError,
)


class FirebasePushProvider(PushProvider):
    APP_NAME = "mausam-push"

    def __init__(
        self,
        *,
        project_id: str,
        credentials_path: str | None = None,
    ):
        self.project_id = project_id

        self.credentials_path = credentials_path

        self.app = self._initialize_firebase()

    def _initialize_firebase(self):
        try:
            return firebase_admin.get_app(self.APP_NAME)

        except ValueError:
            pass

        options = {"projectId": self.project_id}

        if self.credentials_path:
            credential = credentials.Certificate(self.credentials_path)

            return firebase_admin.initialize_app(
                credential,
                options=options,
                name=self.APP_NAME,
            )

        # Uses Application Default Credentials.
        #
        # For example:
        # GOOGLE_APPLICATION_CREDENTIALS
        return firebase_admin.initialize_app(
            options=options,
            name=self.APP_NAME,
        )

    @staticmethod
    def _build_message(
        *,
        registration_id: str,
        registration_type: (PushRegistrationType),
        message: PushMessage,
    ) -> messaging.Message:
        common = {
            "notification": (
                messaging.Notification(
                    title=message.title,
                    body=message.body,
                )
            ),
            "data": message.data,
        }

        if registration_type == PushRegistrationType.FID:
            return messaging.Message(
                **common,
                fid=registration_id,
            )

        return messaging.Message(
            **common,
            token=registration_id,
        )

    def _send_sync(
        self,
        *,
        registration_id: str,
        registration_type: (PushRegistrationType),
        message: PushMessage,
    ) -> str:
        firebase_message = self._build_message(
            registration_id=(registration_id),
            registration_type=(registration_type),
            message=message,
        )

        return messaging.send(
            firebase_message,
            app=self.app,
        )

    async def send(
        self,
        *,
        registration_id: str,
        registration_type: (PushRegistrationType),
        message: PushMessage,
    ) -> PushSendResult:
        try:
            # Firebase Admin's send() performs
            # synchronous network I/O.
            #
            # Move it off FastAPI's async
            # event loop.
            message_id = await asyncio.to_thread(
                self._send_sync,
                registration_id=(registration_id),
                registration_type=(registration_type),
                message=message,
            )

        except messaging.UnregisteredError as exc:
            raise (
                InvalidPushRegistrationError(
                    "Firebase registration is no longer active"
                )
            ) from exc

        except exceptions.UnavailableError as exc:
            raise (
                TemporaryPushProviderError(
                    "Firebase Cloud Messaging is temporarily unavailable"
                )
            ) from exc

        except exceptions.FirebaseError as exc:
            raise PushProviderError("Firebase push delivery failed") from exc

        return PushSendResult(message_id=message_id)
