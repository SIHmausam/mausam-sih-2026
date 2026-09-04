from app.integrations.email.base import EmailProvider


class DisabledEmailProvider(EmailProvider):
    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        return
