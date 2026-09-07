import httpx

from app.integrations.email.base import EmailProvider


class BrevoEmailProvider(EmailProvider):
    def __init__(
        self,
        *,
        api_key: str,
        api_url: str,
        from_email: str,
        from_name: str,
        timeout_seconds: float = 10.0,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.from_email = from_email
        self.from_name = from_name
        self.timeout_seconds = timeout_seconds

    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        payload: dict[str, object] = {
            "sender": {
                "name": self.from_name,
                "email": self.from_email,
            },
            "to": [
                {
                    "email": to_email,
                }
            ],
            "subject": subject,
            "textContent": text_body,
        }

        if html_body is not None:
            payload["htmlContent"] = html_body

        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
        ) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
            )

        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(
                "Brevo email delivery failed "
                f"with status {response.status_code}"
            )