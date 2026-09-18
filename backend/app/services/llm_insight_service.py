from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any, ClassVar, Protocol

from app.schemas.llm import LLMInsightResponse

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    async def generate_json(
        self,
        *,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]: ...


class LLMClientError(Exception):
    """Raised when the LLM cannot generate a valid response."""


class LLMInsightService:
    """
    Generates natural-language explanations for existing Mausam cards.

    IMPORTANT:
    This service is an explanation layer only.

    It does NOT:
    - rank cards
    - select cards
    - determine eligibility
    - modify ML scores
    - calculate weather values
    - replace deterministic card insights
    """

    INSIGHT_CACHE_TTL_SECONDS: ClassVar[int] = 10 * 60

    _insight_cache: ClassVar[dict[str, tuple[float, dict[str, str]]]] = {}

    _cache_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    CARD_FIELDS: ClassVar[dict[str, tuple[str, ...]]] = {
        "temperature": ("temperature_2m",),
        "weather_conditions": ("weather_code",),
        "humidity": ("relative_humidity_2m",),
        "rain_forecast": (
            "precipitation_probability",
            "rain",
        ),
        "wind": ("wind_speed_10m",),
        "air_quality": ("us_aqi",),
        "uv_allergy": (
            "uv_index",
            "us_aqi",
            "relative_humidity_2m",
        ),
        "running_conditions": (
            "temperature_2m",
            "wind_speed_10m",
            "uv_index",
            "precipitation_probability",
        ),
        "surf_conditions": (
            "wave_height",
            "wave_period",
        ),
        "tide_water": ("sea_surface_temperature",),
        "farm_garden": (
            "soil_moisture_0_to_7cm",
            "precipitation_probability",
        ),
        "commute_conditions": (
            "visibility",
            "precipitation_probability",
            "wind_speed_10m",
            "weather_code",
        ),
        "travel_conditions": (
            "precipitation_probability",
            "wind_speed_10m",
            "visibility",
        ),
        "family_school": (
            "precipitation_probability",
            "weather_code",
        ),
        "event_conditions": (
            "precipitation_probability",
            "temperature_2m",
            "relative_humidity_2m",
        ),
    }

    FIELD_METADATA: ClassVar[dict[str, dict[str, str]]] = {
        "temperature_2m": {
            "unit": "°C",
            "meaning": "air temperature",
        },
        "relative_humidity_2m": {
            "unit": "%",
            "meaning": "relative humidity",
        },
        "precipitation_probability": {
            "unit": "%",
            "meaning": "chance of precipitation",
        },
        "rain": {
            "unit": "mm",
            "meaning": "rain amount",
        },
        "wind_speed_10m": {
            "unit": "km/h",
            "meaning": "wind speed",
        },
        "visibility": {
            "unit": "m",
            "meaning": "visibility distance",
        },
        "us_aqi": {
            "unit": "US AQI",
            "meaning": "air quality index",
        },
        "uv_index": {
            "unit": "UV index",
            "meaning": "UV index",
        },
        "soil_moisture_0_to_7cm": {
            "unit": "m³/m³",
            "meaning": "surface soil moisture",
        },
        "wave_height": {
            "unit": "m",
            "meaning": "wave height",
        },
        "wave_period": {
            "unit": "s",
            "meaning": "wave period",
        },
        "sea_surface_temperature": {
            "unit": "°C",
            "meaning": "sea surface temperature",
        },
    }

    UNSUPPORTED_CLASSIFICATION_TERMS: ClassVar[set[str]] = {
        "high",
        "low",
        "moderate",
        "light",
        "strong",
        "warm",
        "cool",
        "hot",
        "cold",
        "comfortable",
        "uncomfortable",
        "small",
        "large",
        "rough",
        "calm",
        "good",
        "poor",
        "acceptable",
        "healthy",
        "unhealthy",
        "favorable",
        "unfavorable",
        "suitable",
        "unsuitable",
        "safe",
        "unsafe",
    }

    FALLBACK_FIELD_ORDER: ClassVar[dict[str, tuple[str, ...]]] = {
        "temperature": ("temperature_2m",),
        "weather_conditions": ("weather_code",),
        "humidity": ("relative_humidity_2m",),
        "rain_forecast": (
            "precipitation_probability",
            "rain",
        ),
        "wind": ("wind_speed_10m",),
        "air_quality": ("us_aqi",),
        "uv_allergy": (
            "uv_index",
            "relative_humidity_2m",
        ),
        "running_conditions": (
            "temperature_2m",
            "precipitation_probability",
        ),
        "surf_conditions": (
            "wave_height",
            "wave_period",
        ),
        "tide_water": ("sea_surface_temperature",),
        "farm_garden": (
            "soil_moisture_0_to_7cm",
            "precipitation_probability",
        ),
        "commute_conditions": (
            "visibility",
            "precipitation_probability",
        ),
        "travel_conditions": (
            "precipitation_probability",
            "wind_speed_10m",
        ),
        "family_school": ("precipitation_probability",),
        "event_conditions": (
            "precipitation_probability",
            "temperature_2m",
        ),
    }

    WEATHER_CODE_DESCRIPTIONS: ClassVar[dict[int, str]] = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "fog",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        56: "light freezing drizzle",
        57: "dense freezing drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        66: "light freezing rain",
        67: "heavy freezing rain",
        71: "slight snowfall",
        73: "moderate snowfall",
        75: "heavy snowfall",
        77: "snow grains",
        80: "slight rain showers",
        81: "moderate rain showers",
        82: "violent rain showers",
        85: "slight snow showers",
        86: "heavy snow showers",
        95: "thunderstorm",
        96: "thunderstorm with slight hail",
        99: "thunderstorm with heavy hail",
    }

    CARD_GUIDANCE: ClassVar[dict[str, str]] = {
        "temperature": ("Focus on practical clothing or outdoor-planning guidance."),
        "weather_conditions": (
            "Explain how the current sky/weather condition may affect "
            "ordinary outdoor plans."
        ),
        "humidity": ("Give practical comfort-oriented guidance for outdoor plans."),
        "rain_forecast": (
            "Help the user decide whether rain preparation may be useful."
        ),
        "wind": ("Explain any practical consideration for ordinary outdoor plans."),
        "air_quality": (
            "Give cautious air-quality awareness guidance. Do not make medical claims."
        ),
        "uv_allergy": (
            "Give cautious outdoor exposure guidance based on supplied UV "
            "and environmental information. Do not make medical claims."
        ),
        "running_conditions": (
            "Give practical weather-related preparation for outdoor exercise "
            "without declaring the activity safe or unsafe."
        ),
        "surf_conditions": (
            "Describe what the marine conditions mean for planning, but do "
            "not declare surfing safe or suitable. Remind the user that local "
            "tide, currents, and beach hazards may also matter."
        ),
        "tide_water": (
            "Give useful planning context for water activities without making "
            "marine safety claims."
        ),
        "farm_garden": (
            "Give cautious monitoring or preparation guidance based on soil "
            "and rain information. Do not prescribe specialized agricultural "
            "treatment."
        ),
        "commute_conditions": ("Give practical weather-related commute preparation."),
        "travel_conditions": ("Give practical weather preparation for travel."),
        "family_school": (
            "Give simple preparation guidance for school or family outings."
        ),
        "event_conditions": ("Give practical planning guidance for outdoor events."),
    }

    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self.llm_client = llm_client

    @staticmethod
    def _build_cache_key(
        *,
        cards: list[dict[str, Any]],
        persona_context: dict[str, Any] | None,
    ) -> str:
        """
        Build a deterministic cache key from the exact information
        that can change the generated insights.
        """

        cache_payload = {
            "cards": [
                {
                    "card": card.get("card"),
                    "rank": card.get("rank"),
                    "score": card.get("score"),
                    "verified_data": card.get("verified_data", {}),
                }
                for card in cards
            ],
            "persona_context": persona_context or {},
        }

        return json.dumps(
            cache_payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    @classmethod
    def _get_cached_insights(
        cls,
        cache_key: str,
    ) -> dict[str, str] | None:
        cached = cls._insight_cache.get(cache_key)

        if cached is None:
            return None

        created_at, insights = cached

        if time.monotonic() - created_at >= cls.INSIGHT_CACHE_TTL_SECONDS:
            cls._insight_cache.pop(cache_key, None)
            return None

        return dict(insights)

    @classmethod
    def _set_cached_insights(
        cls,
        cache_key: str,
        insights: dict[str, str],
    ) -> None:
        cls._insight_cache[cache_key] = (
            time.monotonic(),
            dict(insights),
        )

    async def generate_insights(
        self,
        *,
        cards: list[dict[str, Any]],
        weather_context: dict[str, Any],
        persona_context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """
        Generate LLM explanations for already-selected cards.

        Architecture:
            Selected cards
                ↓
            Controlled verified context
                ↓
            Cache lookup
                ↓
            ONE LLM API request for ALL cards
                ↓
            Validation + grounding
                ↓
            Cache
                ↓
            Return insights

        The LLM never ranks, selects, or changes cards.
        """

        if not cards:
            return {}

        controlled_cards: list[dict[str, Any]] = []

        for card in cards:
            card_name = card.get("card")

            if not card_name:
                continue

            controlled_cards.append(
                {
                    "card": card_name,
                    "rank": card.get("rank"),
                    "score": card.get("score"),
                    "verified_data": self._build_card_context(
                        card=card_name,
                        weather_context=weather_context,
                    ),
                }
            )

        if not controlled_cards:
            return {}

        cache_key = self._build_cache_key(
            cards=controlled_cards,
            persona_context=persona_context,
        )

        cached_insights = self._get_cached_insights(cache_key)

        if cached_insights is not None:
            logger.info(
                "LLM insight cache HIT for %d cards.",
                len(controlled_cards),
            )
            return cached_insights

        logger.info(
            "LLM insight cache MISS for %d cards.",
            len(controlled_cards),
        )

        async with self._cache_lock:
            # Another request may have generated the same result
            # while this request was waiting for the lock.
            cached_insights = self._get_cached_insights(cache_key)

            if cached_insights is not None:
                logger.info("LLM insight cache HIT after lock.")
                return cached_insights

            requested_cards = [card["card"] for card in controlled_cards]

            response_schema = {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "insights": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "card": {
                                    "type": "string",
                                    "enum": requested_cards,
                                },
                                "insight": {
                                    "type": "string",
                                },
                            },
                            "required": [
                                "card",
                                "insight",
                            ],
                        },
                    },
                },
                "required": [
                    "insights",
                ],
            }

            prompt = self._build_prompt(
                cards=controlled_cards,
                persona_context=persona_context,
            )

            try:
                logger.info(
                    "Generating %d insights with ONE LLM API request.",
                    len(controlled_cards),
                )

                raw_response = await asyncio.wait_for(
                    self.llm_client.generate_json(
                        prompt=prompt,
                        response_schema=response_schema,
                    ),
                    timeout=5.0,
                )

                validated = LLMInsightResponse.model_validate(raw_response)

                returned_cards = {
                    item.card for item in validated.insights if item.insight.strip()
                }

                requested_card_set = set(requested_cards)

                if returned_cards != requested_card_set:
                    missing_cards = requested_card_set - returned_cards

                    extra_cards = returned_cards - requested_card_set

                    raise ValueError(
                        "LLM returned incomplete card insights. "
                        f"Missing: {sorted(missing_cards)}; "
                        f"Extra: {sorted(extra_cards)}"
                    )

                verified_context_by_card = {
                    card["card"]: card["verified_data"] for card in controlled_cards
                }

                grounded_insights: dict[str, str] = {}

                for item in validated.insights:
                    card_name = item.card
                    insight = item.insight.strip()

                    if not insight:
                        continue

                    verified_data = verified_context_by_card.get(
                        card_name,
                        {},
                    )

                    if self._contains_unsupported_classification(
                        insight=insight,
                        verified_data=verified_data,
                    ):
                        logger.warning(
                            "Rejected unsupported LLM classification for card %s.",
                            card_name,
                        )

                        insight = self._build_factual_fallback(
                            card=card_name,
                            verified_data=verified_data,
                        )

                    grounded_insights[card_name] = insight

                if set(grounded_insights) != requested_card_set:
                    missing_cards = requested_card_set - set(grounded_insights)

                    raise ValueError(
                        "Grounded insight generation is incomplete. "
                        f"Missing: {sorted(missing_cards)}"
                    )

                self._set_cached_insights(
                    cache_key,
                    grounded_insights,
                )

                logger.info(
                    "Generated and cached %d insights.",
                    len(grounded_insights),
                )

                return grounded_insights

            except Exception:
                import traceback

                logger.exception(
                    "LLM insight generation failed",
                )

                traceback.print_exc()

                fallback_insights: dict[str, str] = {}

                for card in controlled_cards:
                    card_name = card["card"]

                    fallback_insights[card_name] = self._build_factual_fallback(
                        card=card_name,
                        verified_data=card.get(
                            "verified_data",
                            {},
                        ),
                    )

                return fallback_insights

    @staticmethod
    def _build_recommendation(
        *,
        card: str,
        weather_context: dict[str, Any],
    ) -> str | None:

        if card == "rain_forecast":
            probability = weather_context.get("precipitation_probability")

            if isinstance(probability, (int, float)) and probability >= 30:
                return "Keep rain protection available and keep outdoor plans flexible."

            return None

        if card == "humidity":
            humidity = weather_context.get("relative_humidity_2m")

            if isinstance(humidity, (int, float)) and humidity >= 80:
                return (
                    "For outdoor plans, breathable clothing "
                    "and flexibility may improve comfort."
                )

            return None

        if card == "temperature":
            temperature = weather_context.get("temperature_2m")

            if isinstance(temperature, (int, float)) and temperature >= 32:
                return (
                    "For longer outdoor plans, consider "
                    "lighter clothing and cooler times of day."
                )

            if isinstance(temperature, (int, float)) and temperature <= 15:
                return "Consider carrying an extra layer for outdoor plans."

            return None

        if card == "surf_conditions":
            return (
                "Use the marine conditions as one part of "
                "your planning and check local tide, currents, "
                "beach hazards, and lifeguard information "
                "before deciding to surf."
            )

        if card == "tide_water":
            return (
                "Use the sea conditions as planning context "
                "and check local marine information before "
                "water activities."
            )

        if card == "wind":
            wind_speed = weather_context.get("wind_speed_10m")

            if isinstance(wind_speed, (int, float)) and wind_speed >= 25:
                return (
                    "Account for wind when planning exposed "
                    "outdoor activities and secure loose items."
                )

            return None

        if card == "air_quality":
            return (
                "Use the air-quality reading when planning "
                "long outdoor activities and check local "
                "air-quality guidance if needed."
            )

        if card == "uv_allergy":
            uv_index = weather_context.get("uv_index")

            if isinstance(uv_index, (int, float)) and uv_index >= 3:
                return (
                    "Consider sun protection if you will be "
                    "outdoors for an extended period."
                )

            return None

        if card == "weather_conditions":
            return "Keep outdoor plans flexible if weather conditions change."

        return None

    @classmethod
    def _build_card_context(
        cls,
        *,
        card: str,
        weather_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Return only the verified fields relevant to this card.

        No values are calculated or inferred here.
        Missing fields remain absent.
        """

        fields = cls.CARD_FIELDS.get(card)

        if not fields:
            return {}

        source = weather_context

        current = weather_context.get("current")

        if isinstance(current, dict):
            source = {
                **weather_context,
                **current,
            }

        verified_data: dict[str, Any] = {}

        for field in fields:
            if field in source and source[field] is not None:
                field_data: dict[str, Any] = {
                    "value": source[field],
                }

                if field == "weather_code":
                    try:
                        weather_code = int(source[field])
                    except (TypeError, ValueError):
                        weather_code = None

                    if weather_code is not None:
                        description = cls.WEATHER_CODE_DESCRIPTIONS.get(weather_code)

                        if description:
                            field_data["interpretation"] = description

                metadata = cls.FIELD_METADATA.get(field)

                if metadata:
                    field_data.update(metadata)

                verified_data[field] = field_data

        guidance = cls.CARD_GUIDANCE.get(card)

        if guidance:
            verified_data["_guidance"] = guidance

        recommendation = cls._build_recommendation(
            card=card,
            weather_context=source,
        )

        if recommendation:
            verified_data["_recommendation"] = recommendation

        return verified_data

    @classmethod
    def _contains_unsupported_classification(
        cls,
        *,
        insight: str,
        verified_data: dict[str, Any],
    ) -> bool:
        normalized_insight = insight.lower()

        allowed_interpretations: list[str] = []

        for field_data in verified_data.values():
            if not isinstance(field_data, dict):
                continue

            interpretation = field_data.get("interpretation")

            if isinstance(interpretation, str):
                allowed_interpretations.append(interpretation.lower())

        interpretation_text = " ".join(allowed_interpretations)

        for term in cls.UNSUPPORTED_CLASSIFICATION_TERMS:
            if not re.search(
                rf"\b{re.escape(term)}\b",
                normalized_insight,
            ):
                continue

            if re.search(
                rf"\b{re.escape(term)}\b",
                interpretation_text,
            ):
                continue

            return True

        return False

    @staticmethod
    def _format_verified_measurement(
        *,
        field: str,
        data: dict[str, Any],
    ) -> str | None:
        value = data.get("value")

        if value is None:
            return None

        unit = data.get("unit")
        meaning = data.get("meaning")

        if field == "precipitation_probability":
            if unit:
                return f"The chance of precipitation is {value}{unit}."

            return f"The chance of precipitation is {value}."

        if not meaning:
            return None

        if unit:
            return f"{meaning.capitalize()} is {value} {unit}."

        return f"{meaning.capitalize()} is {value}."

    @classmethod
    def _build_factual_fallback(
        cls,
        *,
        card: str,
        verified_data: dict[str, Any],
    ) -> str:
        fields = cls.FALLBACK_FIELD_ORDER.get(
            card,
            (),
        )

        statements: list[str] = []

        for field in fields:
            data = verified_data.get(field)

            if not isinstance(data, dict):
                continue

            statement = cls._format_verified_measurement(
                field=field,
                data=data,
            )

            if statement:
                statements.append(statement)

            if len(statements) == 2:
                break

        if statements:
            return " ".join(statements)

        return "No specific information is available."

    @staticmethod
    def _build_prompt(
        *,
        cards: list[dict[str, Any]],
        persona_context: dict[str, Any] | None,
    ) -> str:
        """
        Build a strict prompt for explanation-only generation.
        """

        persona = (
            persona_context if persona_context else "No persona context is relevant."
        )
        required_cards = [
            card["card"]
            for card in cards
            if isinstance(card, dict) and card.get("card")
        ]

        required_cards_text = "\n".join(f"- {card}" for card in required_cards)
        card_context_blocks = "\n\n".join(
            (
                f"CARD: {card['card']}\n"
                f"VERIFIED DATA: {json.dumps(card['verified_data'], sort_keys=True)}\n"
                f"REQUIRED: Return exactly one insight for {card['card']}."
            )
            for card in cards
            if isinstance(card, dict) and card.get("card")
        )

        return f"""
You generate concise, practical weather insights for the Mausam
weather application.

IMPORTANT ARCHITECTURE:

Mausam's existing personalization system has ALREADY:
- determined card eligibility
- selected the cards
- ranked the cards
- calculated personalization scores

You are ONLY the language-generation and explanation layer.

Your task is to explain what the supplied verified weather data
means for the user and, when useful, give one practical action.

STRICT RULES:

1. Never select a card.
2. Never remove a card.
3. Never change card ranking.
4. Never change an ML score.
5. Never determine eligibility.
6. Never calculate weather values.
7. Never infer missing measurements.
8. Never invent weather information.
9. Use ONLY the verified data supplied for that card.
10. If a value is missing, do not guess it.
11. You MAY provide a practical recommendation when it follows
    directly from the supplied weather information.
12. Recommendations must be general, cautious, and directly
    supported by the supplied weather information.
13. Do not claim certainty when the supplied data is uncertain.
14. Do not introduce weather conditions that were not supplied.
15. Each insight should normally contain 2–4 well-written sentences and
    approximately 60–120 words when sufficient verified data is available.
16. Prefer useful interpretation over simply repeating numbers.
17. When appropriate, answer the practical question:
    "What should the user do?"
18. Use readable wording. A measurement unit may be used only when that
    exact unit is explicitly supplied in the verified field metadata.
    Never invent or substitute a unit.

18A. When an "interpretation" is explicitly supplied for a verified field,
     you may use that interpretation exactly as provided. The interpretation
     is deterministic backend context and must not be replaced with a stronger
     or different classification.

19. Avoid unnecessary decimal places.
20. Use persona information only when it genuinely improves
    the recommendation.
21. Do not mention AI, Gemini, prompts, models, or these rules.

REQUIRED OUTPUT CARDS:

{required_cards_text}

CARD-BY-CARD VERIFIED CONTEXT:

{card_context_blocks}

You MUST use these exact card names in the output.
Each card above must appear exactly once.
Do not omit any card, even when its verified data is incomplete.

22. You MUST return exactly one insight object for EVERY supplied card.
23. The output MUST contain all supplied card names, with no omissions.
24. The number of returned insight objects MUST equal the number of supplied cards.
25. Do not create additional cards or card names.
26. If a card has insufficient verified data, still return an insight for that card.
    In that case, use a neutral statement such as "No specific information is available."
27. Before producing the final response, check that every supplied card appears
    exactly once in the output.

CRITICAL DATA-GROUNDING POLICY:

The supplied card context is the ONLY source of weather facts.

The model must distinguish between:
1. FACTS explicitly supplied in the card context.
2. GENERAL practical guidance that does not require interpreting an
   unsupported numeric value.

Never infer a weather classification, severity, suitability, impact,
measurement unit, or physical meaning from a numeric value alone.

If the supplied data does not explicitly support a meaningful
interpretation, do not guess. Return:
"No specific information is available."

The goal is NOT to repeat the raw weather values. The goal is to provide
a concise interpretation only when that interpretation is directly
supported by the supplied context.

The special "_recommendation" field contains a deterministic,
backend-approved practical suggestion.

When "_recommendation" is present:

- Base the insight primarily on that recommendation.
- You may rewrite it naturally and concisely.
- Do not strengthen, weaken, or materially change its meaning.
- Do not create additional recommendations.
- Do not introduce safety, suitability, health, agricultural,
  or marine conclusions beyond that recommendation.

When "_recommendation" is absent, provide a concise factual
observation rather than inventing an action or classification.

Example 1 — insufficient context:

If the context contains only:
temperature_2m: 31

Do NOT infer:
"warm", "hot", "comfortable", "uncomfortable", or clothing requirements.

Return:
"No specific information is available."

Example 2 — explicit interpretation:

If the context contains:
temperature_2m: 31
temperature_interpretation: "warm"

Then "warm" may be used because the interpretation is explicitly supplied.

Example 3 — precipitation probability:

If the context contains:
precipitation_probability: 35

The model may describe this as a possibility or likelihood of precipitation,
but must not claim that rain will occur or that a particular rainfall
amount is expected.

Example 4 — card-specific context:

If a card contains multiple verified fields, use the relevant verified
fields for that specific card. Do not use information from another card.

Do not reuse the same generic insight across multiple cards when the cards
have different verified fields.

Do not describe precipitation as "light", "moderate", "heavy", or similar
unless that classification is explicitly supplied in the context.

When information is insufficient for a supported interpretation, return:
"No specific information is available."


28. Each insight should normally contain 2–4 sentences.
29. Target approximately 60–120 words when the supplied verified data
    supports a useful explanation. Do not add filler merely to increase length.
    
30. The insight should feel like a premium personalized weather briefing,
    not a raw-data summary.

31. Start with the most meaningful interpretation of the supplied conditions.

32. Connect the verified weather information to the purpose of the card.
    For example:
    - temperature → how the conditions relate to outdoor planning
    - rain_forecast → how precipitation possibility may affect plans
    - wind → how wind conditions relate to outdoor activities
    - air_quality → what the supplied air-quality reading means for planning
    - running_conditions → practical exercise planning
    - commute_conditions → practical weather-related commuting context
    - travel_conditions → weather-related travel preparation
    - farm_garden → observation and monitoring context
    - family_school → simple planning context
    - event_conditions → outdoor event planning
    - surf_conditions → marine planning context

33. Use natural, polished language rather than repetitive templates.

34. Make each insight feel specific to its card and supplied data.

35. When a practical recommendation is supplied through the deterministic
    "_recommendation" field, incorporate it naturally rather than merely
    repeating the raw measurement.

36. Use a confident but measured professional tone.

37. Avoid generic filler such as "Stay safe", "Have a great day", or
    "Keep an eye on the weather" unless directly relevant to the supplied data.

38. Do not repeat the same sentence structure across different cards.

39. Do not invent personal preferences, activities, weather conditions,
    measurements, forecasts, or outcomes.

40. Do not sacrifice factual grounding for engaging language.

41. When sufficient verified information exists, explain:
    what the supplied condition means → why it matters for this card →
    what practical preparation may be useful.

42. Do not make the insight longer merely for the sake of length.

30. The weather card already displays the raw measurement. Do not make the
    insight primarily a repetition of that measurement.

    The insight should primarily answer:
    - What does this condition mean for the user?
    - What practical action or preparation may be useful?

    Mention a numeric measurement only when it materially helps explain the
    recommendation.

30A. Low-risk practical suggestions are allowed when they follow reasonably
     from the supplied weather information.

     Examples of acceptable general guidance include:
     - carrying rain protection when precipitation is possible
     - adjusting outdoor timing based on weather conditions
     - choosing clothing appropriate for current temperature or humidity
     - keeping outdoor plans flexible when weather may affect them
     - checking local tide/current information before marine activities

     Do not turn these suggestions into guarantees or safety claims.

30B. Prefer a useful recommendation over simply repeating values.

     Good:
     "Keep rain protection handy if you're heading out."

     Less useful:
     "Precipitation probability is 47%."

     Good:
     "For outdoor plans, lighter breathable clothing may be more comfortable."

     Less useful:
     "Relative humidity is 89%."

31. Never repeat a numeric weather value in the insight unless it is essential
    to answer the specific request.

31A. When generating an insight, prioritize interpretation over repetition.
      Do not list multiple raw measurements from the card. Select the most
      relevant verified condition and explain its practical significance
      only when that significance is explicitly supported.

32. Do not infer qualitative meaning from a numeric value alone. Do not use
    words such as "low", "high", "moderate", "warm", "cool", "good",
    "poor", "comfortable", "favorable", "suitable", "breezy", "noticeable",
    "light", or "heavy" unless that interpretation is explicitly supported
    by the supplied context.

33. Do not calculate, derive, estimate, compare, classify, or extrapolate
    any value that is not explicitly supplied.

34. Never invent, assume, or substitute measurement units. If a unit is not
    supplied, do not add one.

35. Treat field names and numeric values as data identifiers only. Do not infer
    additional physical meaning, severity, suitability, or impact beyond the
    explicitly supplied context.

36. Do not convert numeric values into qualitative labels such as
    "low", "moderate", "high", "small", "warm", "hot", "manageable",
    "comfortable", "favorable", "suitable", "breezy", "strong",
    "light", "good", "poor", "cool", "damp", or "heavy" unless that
    interpretation is explicitly supported by the supplied context.

    In particular, never describe wind as "strong" or "moderate",
    visibility as "good" or "poor", precipitation as "light",
    "moderate", or "heavy", or any activity condition as "good",
    "suitable", or "favorable" based only on a numeric value.

37. Do not turn weather observations into activity suitability decisions.
    For running, surfing, commuting, travel, family/school, events, or other
    activities, describe verified observations conservatively.

38. For farming, gardening, marine activities, health, or other specialized
    domains, provide only observation, monitoring, or general preparation
    guidance. Do not prescribe specialized actions or decisions.

39. Keep recommendations general and cautious. Do not make medical,
    agricultural, marine, or other specialized decisions.

40. Do not turn a weather observation into a specialized decision.
    For specialized domains, prefer monitoring or preparation guidance
    over prescribing an action.

41. For probability fields, describe probability as likelihood only.
    Do not convert probability into certainty.

42. Do not describe rainfall as certain or "expected" from probability
    alone.

43. Never turn an unlabeled numeric value into a statement such as
    "2 units of rain", "4.2 mm of rain", "4.2 expected rainfall",
    or any equivalent interpretation.

44. Do not predict future changes or relationships between weather
    variables unless that information is explicitly supplied.

45. For activity cards such as running_conditions, surf_conditions,
    commute_conditions, travel_conditions, family_school, and
    event_conditions, describe verified observations conservatively.
    Do not declare the activity suitable or unsuitable unless the
    supplied data explicitly supports that conclusion.

46. For farming/gardening cards, provide observations and cautious
    monitoring guidance only. Do not prescribe agricultural actions
    unless explicitly supported by the supplied data.

47. For sea_surface_temperature, wave_height, wave_period, visibility,
    wind_speed_10m, temperature_2m, and soil_moisture_0_to_7cm, do not
    infer practical suitability or impact from the numeric value when
    its unit or interpretation is not explicitly supplied.

48. When information is incomplete, use the verified fields that are
    available and provide a useful neutral interpretation.

49. If verified measurements are available with explicit units or meanings,
    provide a concise factual observation using those fields.

    Return "No specific information is available." only when no usable
    verified information for that card is supplied.

50. Do not mention AI, LLMs, prompts, or the generation process.

51. ALWAYS return exactly one concise, non-empty insight for every
    supplied card. Never omit, duplicate, or add a card.

52. If some relevant fields are missing, use the verified fields that
    are available. If no relevant fields are available, return:
    "No specific information is available."

53. The number of returned insights MUST exactly equal the number of
    cards in the supplied card_context. Never return null, an empty
    string, an omitted card, or a partial response.

54. Before producing the final response, verify that every supplied card
    appears exactly once and that no additional cards are returned.

55. The response must contain only the requested structured output.
    Do not include explanations, commentary, headings, or text outside
    the required response format.

56. Every insight must be directly grounded in the supplied card context.
    Do not use outside weather information or assumptions.

57. If a card has at least one verified relevant field, generate an
    interpretation using only those verified fields. Do not omit the
    card because other relevant fields are missing.

58. If all relevant fields for a card are unavailable or unusable,
    return exactly "No specific information is available." for that
    card rather than inventing or inferring information.

59. Do not use the same generic insight for multiple different card types
    when their supplied contexts differ. Each card must have an insight
    grounded in its own relevant verified fields.


EXAMPLES OF THE DESIRED STYLE:

The insight should interpret the supplied verified weather data rather than
simply repeating raw values already displayed on the card.

Use the explicit semantic meaning of a supplied field when that meaning is
provided by the field name or surrounding verified context. Do not invent
units, thresholds, classifications, or unsupported implications.

Verified context:
precipitation_probability: 35

Prefer:
"There's some chance of rain, so carrying rain protection could be useful."

Verified context:
uv_index: 7
uv_interpretation: "high"

Prefer:
"UV exposure is high, so consider sun protection if you'll be outdoors."

Verified context:
temperature_2m: 31

Do not:
"It's 31 degrees, so it's warm."

Do not invent a unit or classify the temperature without sufficient
verified context.

Instead, if no supported interpretation can be made:
"No specific information is available."

Verified context:
wave_height: 1.4
wave_period: 9

Do not:
"The waves are moderate and suitable for surfing."

Do not infer suitability, severity, or qualitative classifications from
the numeric values.

If no supported interpretation can be made:
"No specific information is available."

Verified context:
soil_moisture_0_to_7cm: 0.28

Do not:
"Soil moisture is low, so irrigation is needed."

Prefer:
"Monitor soil conditions alongside upcoming weather."

IMPORTANT:

These examples illustrate the required grounding behavior only. Do not
treat the example values as facts about the current weather.

Use only the supplied verified card context.

Do not copy an interpretation unless it is explicitly supported by the
supplied data.

Never invent units, thresholds, qualitative classifications, severity,
suitability judgments, or specialized recommendations.

Do not use data from one card to create an insight for another card unless
that field is explicitly present in that card's supplied context.

When the supplied data is insufficient to support a meaningful insight,
return:
"No specific information is available."

PERSONA CONTEXT:
{persona}

CARDS AND VERIFIED DATA:
{card_context_blocks}
""".strip()
