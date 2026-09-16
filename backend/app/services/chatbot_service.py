from __future__ import annotations

from typing import Any, ClassVar

from redis.asyncio import Redis

from app.integrations.llm.llm_provider import LLMProvider
from app.schemas.weather import WeatherContextResponse


class ChatbotService:
    MAX_QUESTIONS = 20
    COUNTER_TTL_SECONDS = 24 * 60 * 60

    WEATHER_KEYWORDS: ClassVar[set[str]] = {
        "weather",
        "temperature",
        "rain",
        "rainfall",
        "forecast",
        "humidity",
        "wind",
        "aqi",
        "air quality",
        "uv",
        "sunrise",
        "sunset",
        "cloud",
        "cloudy",
        "precipitation",
        "storm",
        "thunder",
        "visibility",
        "dew point",
        "heat",
        "cold",
        "climate",
        "tide",
        "wave",
        "waves",
        "sea",
        "soil moisture",
        "farming",
        "farm",
        "garden",
        "commute",
        "travel",
        "running",
        "run",
        "jog",
        "jogging",
        "exercise",
        "workout",
        "walking",
        "walk",
        "cycling",
        "cycle",
        "surf",
        "surfing",
        "school",
        "children",
        "child",
        "kids",
        "family",
        "event",
        "outdoor event",
        "picnic",
        "outdoor",
        "weather card",
        "mausam",
    }

    APP_KEYWORDS: ClassVar[set[str]] = {
        "app",
        "homepage",
        "personalization",
        "personalized",
        "card",
        "cards",
        "notification",
        "alert",
        "mausam assistant",
    }

    CONTEXT_KEYWORDS: ClassVar[
        dict[str, set[str]]
    ] = {
        "running_conditions": {
            "run",
            "running",
            "jog",
            "jogging",
            "exercise",
            "workout",
            "walk",
            "walking",
            "cycling",
            "cycle",
        },
        "travel_conditions": {
            "travel",
            "travelling",
            "traveling",
            "trip",
            "journey",
            "tour",
            "road trip",
            "flight",
        },
        "commute_conditions": {
            "commute",
            "commuting",
            "office",
            "work",
            "drive",
            "driving",
            "ride",
            "riding",
            "traffic",
            "road",
        },
        "family_school": {
            "school",
            "child",
            "children",
            "kid",
            "kids",
            "family",
            "student",
            "students",
        },
        "farm_garden": {
            "farm",
            "farming",
            "farmer",
            "crop",
            "crops",
            "agriculture",
            "agricultural",
            "garden",
            "gardening",
            "plant",
            "plants",
            "planting",
            "soil",
            "irrigation",
        },
        "surf_conditions": {
            "surf",
            "surfing",
            "wave",
            "waves",
            "sea",
            "ocean",
            "beach",
        },
        "event_conditions": {
            "event",
            "party",
            "picnic",
            "wedding",
            "function",
            "festival",
            "concert",
            "outdoor event",
            "outdoor activity",
        },
    }

    def __init__(
    self,
    *,
    redis: Redis,
    llm_client: LLMProvider,
) -> None:
        self.redis = redis
        self.llm_client = llm_client

    async def ask(
        self,
        *,
        user_id: str,
        session_id: str,
        question: str,
        weather_context: WeatherContextResponse | None = None,
    ) -> tuple[str, int, int]:

        question = question.strip()

        if not question:
            raise ValueError("Question cannot be empty")

        if not self._is_mausam_related(question):
            return (
                (
                    "Please ask a question related to Mausam, weather, "
                "or the Mausam app."
                ),
                0,
                self.MAX_QUESTIONS,
            )

        # -----------------------------------------------------
        # Identify the most relevant weather/activity context.
        # -----------------------------------------------------

        context = self._detect_context(question)

        counter_key = self._counter_key(
            user_id=user_id,
            session_id=session_id,
        )

        count = await self.redis.incr(counter_key)

        if count == 1:
            await self.redis.expire(
                counter_key,
                self.COUNTER_TTL_SECONDS,
            )

        if count > self.MAX_QUESTIONS:
            return (
                (
                    "You have reached the 20-question limit for this "
                "chatbot session. Please start a new session."
                ),
                self.MAX_QUESTIONS,
                0,
            )

        try:
            prompt = self._build_prompt(
                question=question,
                weather_context=weather_context,
                context=context,
            )

            result = await self.llm_client.generate_json(
                prompt=prompt,
                response_schema={
                   "type": "object",
                   "properties": {
                       "answer": {
                          "type": "string",
                        }
                    },
                    "required": ["answer"],
                    "additionalProperties": False,
                }
            )

            answer = result.get("answer")

            if not isinstance(answer, str) or not answer.strip():
                raise ValueError(
                    "LLM returned an empty chatbot answer"
                )

            answer = answer.strip()

        except Exception as exc:   # noqa: BLE001
            print(
                f"\n[CHATBOT LLM ERROR] "
                f"{type(exc).__name__}: {exc}\n"
            )
            answer = self._deterministic_fallback(
                question=question,
                weather_context=weather_context,
                context=context,
            )

        return (
            answer,
            count,
            self.MAX_QUESTIONS - count,
        )

    @classmethod
    def _is_mausam_related(cls, question: str) -> bool:
        normalized = question.lower()

        # Direct keyword matching.
        if any(
            keyword in normalized
            for keyword in cls.WEATHER_KEYWORDS
        ):
            return True

        # Context keywords are also considered Mausam-related.
        for keywords in cls.CONTEXT_KEYWORDS.values():
            if any(keyword in normalized for keyword in keywords):
                return True

        # Application-specific questions.
        return any(
            keyword in normalized
            for keyword in cls.APP_KEYWORDS
        )

    @classmethod
    def _detect_context(cls, question: str) -> str:
        normalized = question.lower()

        # Check specific activity contexts first.
        for context, keywords in cls.CONTEXT_KEYWORDS.items():
            if any(
                keyword in normalized
                for keyword in keywords
            ):
                return context

        # Otherwise classify as general weather.
        return "general_weather"

    @classmethod
    def requires_marine_context(
        cls,
        question: str,
    ) -> bool:
        return (
            cls._detect_context(question)
            == "surf_conditions"
        )

    @classmethod
    def _build_prompt(
        cls,
        *,
        question: str,
        weather_context: WeatherContextResponse | None,
        context: str,
    ) -> str:

        weather_data = cls._weather_context_to_dict(
            weather_context
        )

        context_instructions = {
            "general_weather": (
                "Answer as a general Mausam/weather assistant. "
                "Use the supplied weather data when the question "
                "asks about current conditions."
            ),
            "running_conditions": (
                "The user is asking about running or outdoor exercise. "
                "Use the supplied temperature, wind, UV, humidity, "
                "and precipitation information when available. "
                "Explain the conditions conservatively. "
                "Do not make medical claims or invent safety thresholds."
            ),
            "travel_conditions": (
                "The user is asking about travel. "
                "Use available precipitation, wind, visibility, "
                "and weather-condition information. "
                "Give a practical weather-based assessment without "
                "inventing road, traffic, flight, or travel information."
            ),
            "commute_conditions": (
                "The user is asking about commuting. "
                "Use available visibility, precipitation, wind, "
                "and weather-condition information. "
                "Do not invent traffic or road conditions."
            ),
            "family_school": (
                "The user is asking about children, family, or school. "
                "Use available precipitation and weather-condition data. "
                "Give a practical weather-based explanation without "
                "making medical or child-safety claims."
            ),
            "farm_garden": (
                "The user is asking about farming, gardening, crops, "
                "or soil. Use only supplied weather and soil information. "
                "Do not invent agricultural measurements or provide "
                "unsupported specialized farming advice."
            ),
            "surf_conditions": (
                "The user is asking about surfing or sea conditions. "
                "Report relevant verified wave, swell, sea-temperature, wind, "
                "precipitation, and daylight values exactly as supplied. "
                "Do not classify any numeric value using words such as minimal, "
                "light, strong, mild, rough, calm, high, or low unless an explicit "
                "classification threshold is supplied. "
                "If is_daylight is false, state only that it is currently nighttime "
                "or outside daylight hours. Do not infer that surfing is advised, "
                "not advised, safe, unsafe, suitable, or unsuitable from daylight. "
                "Do not make a surfing recommendation from the supplied measurements. "
                "If the user asks whether they should surf, summarize the verified "
                "conditions and explain that suitability cannot be determined from "
                "weather data alone because local currents, tide timing, beach "
                "hazards, and lifeguard conditions are not supplied."
            ),
            "event_conditions": (
                "The user is asking about an event or outdoor activity. "
                "Use available precipitation, temperature, humidity, "
                "and weather-condition information. "
                "Do not invent venue, crowd, traffic, or event information."
            ),
        }

        instructions = context_instructions.get(
            context,
            context_instructions["general_weather"],
        )

        return f"""
You are the Mausam weather assistant.

The user's question is:

{question}

Detected context:

{context}

Context-specific instructions:

{instructions}

Verified Mausam weather data:

{weather_data}

Rules:

1. Answer only the user's Mausam/weather/app question.
2. Use only information present in the supplied weather data.
3. Never invent weather values.
4. Never claim to have access to information that was not supplied.
5. Do not calculate new weather measurements.
6. Do not change ML personalization, card ranking, or eligibility.
7. You are only explaining the supplied weather information.
8. Only mention missing or unavailable information when the user's question specifically requires that information. Do not mention unrelated missing fields.
. Never expose internal API, schema, database, or variable field names to the user. Convert technical field names such as "us_aqi", "rain_probability", "temperature_2m", and "wind_speed_10m" into natural user-facing terms such as "AQI", "chance of rain", "temperature", and "wind speed".
Do not present weather information as a comma-separated list of raw
measurements. Integrate relevant values naturally into complete sentences.
Use human-friendly units and wording when the units are known.
. Do not mention whether an AQI value is US AQI or European AQI unless the user explicitly asks about the AQI standard.
9. For activity questions, provide a conservative weather-based assessment.
10. Do not provide medical diagnoses or unsupported health/safety claims.
11. Do not assign a unit to a numeric value unless that unit is explicitly
known from the supplied context.

12. Do not convert a raw numeric measurement into qualitative terms such as
"light", "strong", "mild", "rough", "high", or "low" unless an explicit
threshold is supplied.

13. Do not recommend specific safety equipment or techniques unless that
information is explicitly part of the supplied Mausam data.
14. Give a clear, conversational answer in approximately 3–5 sentences.

For weather questions where sufficient verified information is available,
do not answer with only a list of measurements. Explain the answer first,
then connect the relevant weather factors to the user's question in a
natural conversational way. Aim for 3–5 complete sentences and approximately
50–100 words when the available data supports that level of explanation.

Aim for approximately 50–100 words when the supplied information
supports a useful explanation.

Explain the answer first, then briefly mention the relevant verified
weather factors supporting it.

Do not pad the response with unnecessary information.

Only mention unavailable weather information when it is necessary to answer
the user's question. Do not list or mention unrelated missing measurements.
If the specific information requested by the user is unavailable, say so
clearly rather than guessing.

15. Return valid JSON matching the requested schema.

Do not make recommendations from unlabeled numeric measurements.

The field "precipitation_probability" is an explicitly defined percentage
representing the likelihood of precipitation. It may be used directly when
answering precipitation or rain-related questions.

For precipitation-related questions:
- Use precipitation_probability when it is available.
- You may state the percentage directly, for example "35% chance of
  precipitation".
- Do not convert the percentage into unsupported labels such as "low",
  "moderate", or "high" unless an explicit threshold is provided.
- Do not use the raw "rain" measurement as evidence for a recommendation
  unless its unit and meaning are explicitly available.
- Do not use weather_code as evidence unless its meaning is explicitly
  provided in the supplied context.
- If precipitation_probability is available, do not claim that sufficient
  precipitation information is unavailable.

When giving a practical recommendation, clearly identify the verified
weather factor supporting it.

Return exactly:

{{
    "answer": "your concise answer"
}}
""".strip()

    @staticmethod
    def _weather_context_to_dict(
        weather_context: WeatherContextResponse | None,
    ) -> dict[str, Any]:

        if weather_context is None:
            return {
                "available": False,
                "message": "Weather context was not supplied.",
            }

        if not weather_context.available:
            return {
                "available": False,
                "message": getattr(
                    weather_context,
                    "message",
                    "Current weather data is unavailable.",
                ),
            }

        current = weather_context.current

        result: dict[str, Any] = {
            "available": True,
            "current": {},
        }

        if current is not None:
            current_data = result["current"]

            if current.temperature is not None:
                current_data["temperature_c"] = (
                    current.temperature
                )

            if current.apparent_temperature is not None:
                current_data[
                    "apparent_temperature_c"
                ] = current.apparent_temperature

            if current.humidity is not None:
                current_data["humidity_percent"] = (
                    current.humidity
                )

            if current.precipitation is not None:
                current_data["precipitation_mm"] = (
                    current.precipitation
                )

            if current.rain is not None:
                current_data["rain_mm"] = (
                    current.rain
                )

            if current.rain_probability is not None:
                current_data[
                    "precipitation_probability_percent"
                ] = current.rain_probability

            if current.weather_code is not None:
                current_data["weather_code"] = (
                    current.weather_code
                )

            if current.wind_speed is not None:
                current_data["wind_speed_kmh"] = (
                    current.wind_speed
                )

            if current.visibility is not None:
                current_data["visibility_m"] = (
                    current.visibility
                )

            if current.is_daylight is not None:
                current_data["is_daylight"] = (
                    current.is_daylight
                )

            current_uv_index = getattr(
                current,
                "uv_index",
                None,
            )

            if current_uv_index is not None:
                current_data["uv_index"] = (
                    current_uv_index
                )

        air_quality = getattr(
            weather_context,
            "air_quality",
            None,
        )

        if air_quality is not None:
            air_quality_data: dict[str, Any] = {}

            for field in (
                "aqi",
                "us_aqi",
                "uv_index",
            ):
                value = getattr(
                    air_quality,
                    field,
                    None,
                )

                if value is not None:
                    air_quality_data[field] = value

            if air_quality_data:
                result["air_quality"] = (
                    air_quality_data
                )

        marine = getattr(
            weather_context,
            "marine",
            None,
        )

        if (
            marine is not None
            and marine.available
        ):
            marine_data: dict[str, Any] = {}

            if marine.wave_height is not None:
                marine_data["wave_height_m"] = (
                    marine.wave_height
                )

            if marine.wave_direction is not None:
                marine_data[
                    "wave_direction_degrees"
                ] = marine.wave_direction

            if marine.wave_period is not None:
                marine_data[
                    "wave_period_seconds"
                ] = marine.wave_period

            if marine.swell_wave_height is not None:
                marine_data[
                    "swell_wave_height_m"
                ] = marine.swell_wave_height

            if marine.swell_wave_direction is not None:
                marine_data[
                    "swell_wave_direction_degrees"
                ] = marine.swell_wave_direction

            if marine.swell_wave_period is not None:
                marine_data[
                    "swell_wave_period_seconds"
                ] = marine.swell_wave_period

            if marine.sea_level_height_msl is not None:
                marine_data[
                    "sea_level_height_msl_m"
                ] = marine.sea_level_height_msl

            if marine.sea_surface_temperature is not None:
                marine_data[
                    "sea_surface_temperature_c"
                ] = marine.sea_surface_temperature

            if marine_data:
                result["marine"] = marine_data

        return result

    @classmethod
    def _deterministic_fallback(
        cls,
        *,
        question: str,
        weather_context: WeatherContextResponse | None,
        context: str,
    ) -> str:

        if (
            weather_context is None
            or not weather_context.available
        ):
            return (
                "Current Mausam weather data is not available right now. "
                "Please try again shortly."
            )

        normalized = question.lower()
        current = weather_context.current

        if context == "running_conditions":

            parts = []

            if current.temperature is not None:
                parts.append(
                    f"the temperature is {current.temperature}°C"
                )

            if current.wind_speed is not None:
                parts.append(
                    f"wind speed is {current.wind_speed}"
                )

            if current.rain_probability is not None:
                parts.append(
                    f"rain probability is "
                    f"{current.rain_probability}%"
                )

            if parts:
                return (
                    "Based on the available Mausam conditions, "
                    + ", ".join(parts)
                    + ". Consider these conditions before running."
                )

            return (
                "Running-related weather information is "
                "not available right now."
            )

        if context == "travel_conditions":

            parts = []

            if current.temperature is not None:
                parts.append(
                    f"temperature is {current.temperature}°C"
                )

            if current.wind_speed is not None:
                parts.append(
                    f"wind speed is {current.wind_speed}"
                )

            if current.visibility is not None:
                parts.append(
                    f"visibility is {current.visibility}"
                )

            if current.rain_probability is not None:
                parts.append(
                    f"rain probability is "
                    f"{current.rain_probability}%"
                )

            if parts:
                return (
                    "Based on the available Mausam data, "
                    + ", ".join(parts)
                    + "."
                )

            return (
                "Travel-related weather information is "
                "not available right now."
            )

        if context == "commute_conditions":

            parts = []

            if current.visibility is not None:
                parts.append(
                    f"visibility is {current.visibility}"
                )

            if current.wind_speed is not None:
                parts.append(
                    f"wind speed is {current.wind_speed}"
                )

            if current.rain_probability is not None:
                parts.append(
                    f"rain probability is "
                    f"{current.rain_probability}%"
                )

            if parts:
                return (
                    "Based on the available Mausam data, "
                    + ", ".join(parts)
                    + "."
                )

            return (
                "Commute-related weather information is "
                "not available right now."
            )

        if context == "family_school":

            parts = []

            if current.rain_probability is not None:
                parts.append(
                    f"rain probability is "
                    f"{current.rain_probability}%"
                )

            if current.temperature is not None:
                parts.append(
                    f"temperature is {current.temperature}°C"
                )

            if parts:
                return (
                    "Based on the available Mausam conditions, "
                    + ", ".join(parts)
                    + "."
                )

            return (
                "School and family-related weather information "
                "is not available right now."
            )

        if context == "event_conditions":

            parts = []

            if current.temperature is not None:
                parts.append(
                    f"temperature is {current.temperature}°C"
                )

            if current.humidity is not None:
                parts.append(
                    f"humidity is {current.humidity}%"
                )

            if current.rain_probability is not None:
                parts.append(
                    f"rain probability is "
                    f"{current.rain_probability}%"
                )

            if parts:
                return (
                    "Based on the available Mausam conditions, "
                    + ", ".join(parts)
                    + "."
                )

            return (
                "Event-related weather information is "
                "not available right now."
            )

        if "temperature" in normalized:
            if current.temperature is not None:
                return (
                    f"The current temperature is "
                    f"{current.temperature}°C."
                )

            return "The current temperature is not available."

        if "humidity" in normalized:
            if current.humidity is not None:
                return (
                    f"The current humidity is "
                    f"{current.humidity}%."
                )

            return "The current humidity is not available."

        if (
            "rain probability" in normalized
            or "chance of rain" in normalized
        ):
            if current.rain_probability is not None:
                return (
                    f"The current rain probability is "
                    f"{current.rain_probability}%."
                )

            return (
                "The current rain probability is not available."
            )

        if "rain" in normalized or "rainfall" in normalized:
            if current.rain is not None:
                return f"Current rain is {current.rain}."

            if current.precipitation is not None:
                return (
                    f"Current precipitation is "
                    f"{current.precipitation}."
                )

            return (
                "Current rain information is not available."
            )

        if "wind" in normalized:
            if current.wind_speed is not None:
                return (
                    f"The current wind speed is "
                    f"{current.wind_speed}."
                )

            return "The current wind speed is not available."

        if "visibility" in normalized:
            if current.visibility is not None:
                return (
                    f"Current visibility is "
                    f"{current.visibility}."
                )

            return (
                "Current visibility information is not available."
            )

        if (
            "aqi" in normalized
            or "air quality" in normalized
        ):
            air_quality = weather_context.air_quality

            if air_quality is not None:

                if air_quality.aqi is not None:
                    return (
                        f"The current AQI is "
                        f"{air_quality.aqi}."
                    )

                if air_quality.us_aqi is not None:
                    return (
                        f"The current US AQI is "
                        f"{air_quality.us_aqi}."
                    )

            return (
                "Current air-quality information "
                "is not available."
            )

        if "uv" in normalized:
            air_quality = weather_context.air_quality

            if (
                air_quality is not None
                and air_quality.uv_index is not None
            ):
                return (
                    f"The current UV index is "
                    f"{air_quality.uv_index}."
                )

            uv_index = getattr(
                current,
                "uv_index",
                None,
            )

            if uv_index is not None:
                return (
                    f"The current UV index is "
                    f"{uv_index}."
                )

            return (
                "The current UV index is not available."
            )

        return (
            "The Mausam assistant is temporarily unavailable, "
            "so I can only provide verified current Mausam "
            "weather values right now."
        )

    @staticmethod
    def _counter_key(
        *,
        user_id: str,
        session_id: str,
    ) -> str:
        return f"chatbot:questions:{user_id}:{session_id}"