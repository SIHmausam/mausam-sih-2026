import asyncio

from dotenv import load_dotenv

from app.integrations.llm.gemini_client import GeminiClient
from app.integrations.llm.groq_client import GroqClient
from app.integrations.llm.llm_provider import FallbackLLMProvider
from app.services.llm_insight_service import LLMInsightService


load_dotenv()


async def run_test(service, title, cards, weather_context):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    insights = await service.generate_insights(
        cards=cards,
        weather_context=weather_context,
        persona_context={
            "personas": ["farmer"],
        },
    )

    print("RAW INSIGHTS:", repr(insights))

    for card in cards:
        card_name = card["card"]

        print(f"\n{card_name}:")
        print(f"  {insights.get(card_name, 'NO INSIGHT GENERATED')}")


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
        {
            "card": "farm_garden",
            "rank": 1,
            "score": 0.95,
        },
        {
            "card": "rain_forecast",
            "rank": 2,
            "score": 0.90,
        },
    ]

    # TEST 1: Low soil moisture + low rain probability
    await run_test(
        service,
        "TEST 1 — LOW SOIL MOISTURE / LOW RAIN",
        cards,
        {
            "soil_moisture_0_to_7cm": 0.15,
            "precipitation_probability": 10.0,
            "rain": 0.0,
        },
    )

    # TEST 2: Higher soil moisture + high rain probability
    await run_test(
        service,
        "TEST 2 — HIGHER SOIL MOISTURE / HIGH RAIN",
        cards,
        {
            "soil_moisture_0_to_7cm": 0.35,
            "precipitation_probability": 80.0,
            "rain": 4.2,
        },
    )

    # TEST 3: Missing soil moisture
    await run_test(
        service,
        "TEST 3 — MISSING SOIL MOISTURE",
        cards,
        {
            "precipitation_probability": 60.0,
            "rain": 2.0,
        },
    )

    # TEST 4: Missing rainfall information
    await run_test(
        service,
        "TEST 4 — MISSING RAIN DATA",
        cards,
        {
            "soil_moisture_0_to_7cm": 0.22,
        },
    )


if __name__ == "__main__":
    asyncio.run(main())
