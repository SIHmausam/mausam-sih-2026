import asyncio
import os

from dotenv import load_dotenv

from app.integrations.llm.gemini_client import GeminiClient
from app.integrations.llm.groq_client import GroqClient
from app.integrations.llm.llm_provider import FallbackLLMProvider
from app.services.llm_insight_service import LLMInsightService


load_dotenv()


async def main():
    groq_client = GroqClient()
    gemini_client = GeminiClient()

    llm_client = FallbackLLMProvider(
        primary=groq_client,
        secondary=gemini_client,
    )

    service = LLMInsightService(
        llm_client=llm_client,
    )

    cards = [
        {"card": "temperature", "rank": 1, "score": 0.95},
        {"card": "weather_conditions", "rank": 2, "score": 0.92},
        {"card": "humidity", "rank": 3, "score": 0.88},
        {"card": "rain_forecast", "rank": 4, "score": 0.85},
        {"card": "wind", "rank": 5, "score": 0.82},
        {"card": "air_quality", "rank": 6, "score": 0.80},
        {"card": "uv_allergy", "rank": 7, "score": 0.78},
        {"card": "running_conditions", "rank": 8, "score": 0.76},
        {"card": "surf_conditions", "rank": 9, "score": 0.74},
        {"card": "tide_water", "rank": 10, "score": 0.72},
        {"card": "farm_garden", "rank": 11, "score": 0.70},
        {"card": "commute_conditions", "rank": 12, "score": 0.68},
        {"card": "travel_conditions", "rank": 13, "score": 0.66},
        {"card": "family_school", "rank": 14, "score": 0.64},
        {"card": "event_conditions", "rank": 15, "score": 0.62},
    ]

    weather_context = {
        "temperature_2m": 31.0,
        "relative_humidity_2m": 58.0,
        "precipitation_probability": 35.0,
        "rain": 0.2,
        "wind_speed_10m": 14.0,
        "visibility": 8500.0,
        "weather_code": 2,
        "us_aqi": 118.0,
        "uv_index": 7.0,
        "soil_moisture_0_to_7cm": 0.28,
        "wave_height": 1.4,
        "wave_period": 9.0,
        "sea_surface_temperature": 28.0,
    }

    persona_context = {
        "personas": [
            "health_conscious",
            "fitness",
            "surfer",
            "traveler",
            "parents_families",
            "farmer",
            "commuter",
            "event_planner",
        ]
    }

    print("Groq model:", os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"))
    print("Gemini model:", os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))
    print("\nGenerating Mausam insights...")
    print("=" * 80)

    insights = await service.generate_insights(
        cards=cards,
        weather_context=weather_context,
        persona_context=persona_context,
    )

    for card in cards:
        name = card["card"]

        print(f"\n{name.upper()}")
        print("-" * 80)
        print(insights.get(name, "NO INSIGHT GENERATED"))

    print("\n" + "=" * 80)
    print(f"Generated: {len(insights)}/{len(cards)} insights")

    expected_cards = {card["card"] for card in cards}
    generated_cards = set(insights.keys())

    if generated_cards == expected_cards:
        print("15-card insight generation: PASS")
    else:
        print("15-card insight generation: FAIL")


if __name__ == "__main__":
    asyncio.run(main())
