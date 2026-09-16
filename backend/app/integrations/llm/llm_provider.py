from __future__ import annotations

from typing import Any, Protocol


class LLMProviderError(Exception):
    """Raised when all configured LLM providers fail."""


class LLMProvider(Protocol):

    async def generate_json(
        self,
        *,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:
        ...


class FallbackLLMProvider:
    """
    Groq is the primary provider.
    Gemini is the secondary provider.

    If Groq fails, Gemini is attempted.
    If both fail, the caller receives an error and
    can use its deterministic fallback.
    """

    def __init__(
        self,
        *,
        primary: LLMProvider,
        secondary: LLMProvider,
    ) -> None:

        self.primary = primary
        self.secondary = secondary

    async def generate_json(
        self,
        *,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:

        try:
            return await self.primary.generate_json(
                prompt=prompt,
                response_schema=response_schema,
            )

        except Exception as primary_error:  # noqa: BLE001

            try:
                return await self.secondary.generate_json(
                    prompt=prompt,
                    response_schema=response_schema,
                )

            except Exception as secondary_error:

                raise LLMProviderError(
                    "All LLM providers failed. "
                    f"Primary: {primary_error}; "
                    f"Secondary: {secondary_error}"
                ) from secondary_error