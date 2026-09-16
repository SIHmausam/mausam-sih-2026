from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(".env")


class GeminiClientError(Exception):
    """Raised when Gemini cannot generate a valid response."""


class GeminiClient:
    """Thin wrapper around the Gemini API."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash",
        )

        self.timeout = float(
            os.getenv(
                "LLM_REQUEST_TIMEOUT_SECONDS",
                "10",
            )
        )

        if not self.api_key:
            raise GeminiClientError(
                "GEMINI_API_KEY is not configured"
            )

        self.client = genai.Client(
            api_key=self.api_key,
        )

    async def generate_json(
        self,
        *,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:

        if not prompt.strip():
            raise GeminiClientError(
                "Gemini prompt cannot be empty"
            )

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._generate,
                    prompt,
                    response_schema,
                ),
                timeout=self.timeout,
            )

        except TimeoutError as exc:
            raise GeminiClientError(
                "Gemini request timed out"
            ) from exc

        except GeminiClientError:
            raise

        except Exception as exc:
            raise GeminiClientError(
                f"Gemini request failed: {exc}"
            ) from exc

        return response
    def _sanitize_schema(
           self,
           schema: dict[str, Any],
           ) -> dict[str, Any]:
               """Convert generic JSON Schema into Gemini-compatible schema."""
               sanitized = dict(schema)

               sanitized.pop("additionalProperties", None)

               if "properties" in sanitized:
                  sanitized["properties"] = {
                  name: self._sanitize_schema(value)
                  for name, value in sanitized["properties"].items()
                }

               if "items" in sanitized and isinstance(sanitized["items"], dict):
                    sanitized["items"] = self._sanitize_schema(
                       sanitized["items"]
                    )

               return sanitized


    def _generate(
        self,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=self._sanitize_schema(response_schema),
                ),
            )

        except Exception as exc:
            raise GeminiClientError(
                f"Gemini API request failed: {exc}"
            ) from exc

        if not response.text:
            raise GeminiClientError(
                "Gemini returned an empty response"
            )

        try:
            result = json.loads(response.text)

        except json.JSONDecodeError as exc:
            raise GeminiClientError(
                "Gemini returned invalid JSON"
            ) from exc

        if not isinstance(result, dict):
            raise GeminiClientError(
                "Gemini response must be a JSON object"
            )

        return result
