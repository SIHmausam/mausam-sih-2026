import asyncio

from app.integrations.llm.gemini_client import GeminiClient
from app.integrations.llm.groq_client import GroqClient
from app.integrations.llm.llm_provider import FallbackLLMProvider
from app.schemas.weather import WeatherContextResponse
from app.services.chatbot_service import ChatbotService


class FakeRedis:
    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def incr(self, key):
        self.data[key] = int(self.data.get(key, 0)) + 1
        return self.data[key]

    async def expire(self, key, seconds):
        return True


async def main():
    question = (
    "Can I go out for drive right now?"
    )

    weather_context = WeatherContextResponse(
        latitude=28.6139,
        longitude=77.2090,
        available=True,
        current={
            "latitude": 28.6139,
            "longitude": 77.2090,
            "temperature_2m": 31.0,
            "relative_humidity_2m": 58.0,
            "rain_probability": 35.0,
            "rain": 0.2,
            "wind_speed_10m": 14.0,
            "visibility": 8500.0,
            "weather_code": 2,
            "uv_index": 7.0,
        },
        air_quality={
    "latitude": 28.6139,
    "longitude": 77.2090,
    "us_aqi": 118.0,
},
        hourly=[],
        daily=[],
    )

    provider = FallbackLLMProvider(
        primary=GroqClient(),
        secondary=GeminiClient(),
    )

    service = ChatbotService(
        redis=FakeRedis(),
        llm_client=provider,
    )

    answer, used, remaining = await service.ask(
        user_id="final_test_user",
        session_id="final_test_session",
        question=question,
        weather_context=weather_context,
    )

    print("\n" + "=" * 80)
    print("FINAL MAUSAM CHATBOT TEST")
    print("=" * 80)
    print("\nQUESTION:")
    print(question)
    print("\nCHATBOT:")
    print(answer)
    print(f"\nQUESTIONS USED: {used}/20")
    print(f"QUESTIONS REMAINING: {remaining}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
