from __future__ import annotations

import json
from typing import Any, ClassVar, Protocol

from app.schemas.llm import LLMInsightResponse


class LLMClient(Protocol):
    async def generate_json(
        self,
        *,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:
        ...


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

    # Exact card -> verified weather fields used by the
    # existing Phase 2 deterministic insight system.
    CARD_FIELDS: ClassVar[
        dict[str, tuple[str, ...]]
    ] = {
        "temperature": (
            "temperature_2m",
        ),
        "weather_conditions": (
            "weather_code",
        ),
        "humidity": (
            "relative_humidity_2m",
        ),
        "rain_forecast": (
            "precipitation_probability",
            "rain",
        ),
        "wind": (
            "wind_speed_10m",
        ),
        "air_quality": (
            "us_aqi",
        ),
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
        "tide_water": (
            "sea_surface_temperature",
        ),
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


    def __init__(
       self,
       llm_client: LLMClient,
    ) -> None:
        self.llm_client = llm_client

    async def generate_insights(
        self,
        *,
        cards: list[dict[str, Any]],
        weather_context: dict[str, Any],
        persona_context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """
        Generate LLM explanations for already-selected cards.

        The input cards are treated as authoritative. This method
        never changes their ordering, score, or eligibility.
        """

        if not cards:
            return {}

        controlled_cards = []

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

        batch_size = 5
        all_insights: list[dict[str, str]] = []

        try:
            for start in range(0, len(controlled_cards), batch_size):
                batch = controlled_cards[start:start + batch_size]
                

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
                                   "enum": [
                                       card["card"]
                                       for card in batch
                                    ],
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
                    cards=batch,
                    persona_context=persona_context,
                )

                raw_response = await self.llm_client.generate_json(
                    prompt=prompt,
                    response_schema=response_schema,
                )

                validated = LLMInsightResponse.model_validate(
                    raw_response
                )

                requested_batch_cards = {
                    card["card"]
                    for card in batch
                }

                returned_batch_cards = {
                    item.card
                    for item in validated.insights
                    if item.insight.strip()
                }

                if returned_batch_cards != requested_batch_cards:
                    missing_cards = (
                        requested_batch_cards - returned_batch_cards
                    )
                    extra_cards = (
                        returned_batch_cards - requested_batch_cards
                    )

                    raise ValueError(
                        "LLM returned incomplete card insights for batch. "
                        f"Missing: {sorted(missing_cards)}; "
                        f"Extra: {sorted(extra_cards)}"
                    )

                all_insights.extend(
                    {
                        "card": item.card,
                        "insight": item.insight.strip(),
                    }
                    for item in validated.insights
                    if item.insight.strip()
                )

        except Exception as exc:  # noqa: BLE001
            import traceback

            print("\nLLM INSIGHT ERROR:")
            print(repr(exc))
            traceback.print_exc()
            return {}

        requested_cards = {
            card["card"]
            for card in controlled_cards
        }

        returned_cards = {
            item["card"]
            for item in all_insights
        }

        if returned_cards != requested_cards:
            missing_cards = requested_cards - returned_cards
            extra_cards = returned_cards - requested_cards

            raise ValueError(
                "LLM returned incomplete card insights. "
                f"Missing: {sorted(missing_cards)}; "
                f"Extra: {sorted(extra_cards)}"
            )

        return {
            item["card"]: item["insight"]
            for item in all_insights
            if (
                item["card"] in requested_cards
                and item["insight"].strip()
            )
        }


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
                verified_data[field] = source[field]

        return verified_data

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
            persona_context
            if persona_context
            else "No persona context is relevant."
        )
        required_cards = [
            card["card"]
            for card in cards
            if isinstance(card, dict) and card.get("card")
        ]

        required_cards_text = "\n".join(
            f"- {card}"
            for card in required_cards
        )
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
15. Keep each insight concise: normally 1-2 sentences.
16. Prefer useful interpretation over simply repeating numbers.
17. When appropriate, answer the practical question:
    "What should the user do?"
18. Use readable wording, but NEVER add or assume a measurement unit.
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


28. Each insight must contain only 1–2 short sentences.
29. Keep each insight concise and suitable for direct display inside
    a weather card.

30. Do not restate raw measurements from the card. The card already displays
    the factual weather values. The insight must primarily provide a concise
    interpretation or practical observation.

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

49. If the available fields do not explicitly support a meaningful
interpretation, return:
    "No specific information is available."

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
{cards}
""".strip()
