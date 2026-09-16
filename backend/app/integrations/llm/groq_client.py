from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from groq import Groq


class GroqClientError(Exception):
    """Raised when Groq cannot generate a valid response."""


class GroqClient:
    """Thin wrapper around the Groq API."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        )
        self.timeout = float(
            os.getenv(
                "GROQ_REQUEST_TIMEOUT_SECONDS",
                "10",
            )
        )

        if not self.api_key:
            raise GroqClientError(
                "GROQ_API_KEY is not configured"
            )

        self.client = Groq(
            api_key=self.api_key,
        )
    @staticmethod
    def _sanitize_schema(schema: Any) -> Any:
        if isinstance(schema, dict):
            result = {
                key: GroqClient._sanitize_schema(value)
                for key, value in schema.items()
            }

            if result.get("type") == "object":
                result["additionalProperties"] = False

            return result

        if isinstance(schema, list):
            return [
                GroqClient._sanitize_schema(item)
                for item in schema
            ]

        return schema

    async def generate_json(
        self,
        *,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:

        if not prompt.strip():
            raise GroqClientError(
                "Groq prompt cannot be empty"
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
            raise GroqClientError(
                "Groq request timed out"
            ) from exc

        except GroqClientError:
            raise

        except Exception as exc:
            raise GroqClientError(
                f"Groq request failed: {exc}"
            ) from exc

        return response

    def _generate(
        self,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:

        response_schema = self._sanitize_schema(response_schema)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are the Mausam weather assistant. "
                            "Follow the supplied instructions exactly."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                

                
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "mausam_response",
                        "strict": True,
                        "schema": response_schema,
                    },
                },
            )

        except Exception as exc:
            raise GroqClientError(
                f"Groq API request failed: {exc}"
            ) from exc

        content = response.choices[0].message.content

        if not content:
            raise GroqClientError(
                "Groq returned an empty response"
            )

        try:
            result = json.loads(content)

        except json.JSONDecodeError as exc:
            raise GroqClientError(
                "Groq returned invalid JSON"
            ) from exc

        if not isinstance(result, dict):
            raise GroqClientError(
                "Groq response must be a JSON object"
            )

        return result
