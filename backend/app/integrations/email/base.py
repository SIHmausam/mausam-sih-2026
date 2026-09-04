from abc import ABC, abstractmethod


class EmailProvider(ABC):
    @abstractmethod
    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        raise NotImplementedError
