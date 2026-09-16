from types import SimpleNamespace

import pytest

from app.services.personalization_service import (
    PersonalizationService,
)


class FakeLLMInsightService:
    def __init__(
        self,
        insights: dict[str, str],
    ) -> None:
        self.insights = insights
        self.calls = []

    async def generate_insights(
        self,
        *,
        cards,
        weather_context,
        persona_context,
    ):
        self.calls.append(
            {
                "cards": cards,
                "weather_context": weather_context,
                "persona_context": persona_context,
            }
        )

        return self.insights


@pytest.mark.asyncio
async def test_llm_insights_replace_ml_insights():
    llm_service = FakeLLMInsightService(
        {
            "temperature": "LLM temperature insight",
            "rain_forecast": "LLM rain insight",
        }
    )

    service = object.__new__(
        PersonalizationService
    )

    service.llm_insight_service = (
        llm_service
    )

    ml_cards = [
        SimpleNamespace(
            card="temperature",
            rank=1,
            score=0.9,
            insight="Original temperature insight",
        ),
        SimpleNamespace(
            card="rain_forecast",
            rank=2,
            score=0.8,
            insight="Original rain insight",
        ),
    ]

    weather = SimpleNamespace(
        model_dump=lambda **_: {
            "temperature_2m": 30.0,
            "precipitation_probability": 40.0,
        }
    )

    insights = await service._generate_llm_insights(
        ml_cards=ml_cards,
        weather=weather,
        personas=["traveler"],
    )

    cards = service._translate_ml_cards(
        ml_cards,
        llm_insights=insights,
    )

    assert cards[0].insight == (
        "LLM temperature insight"
    )

    assert cards[1].insight == (
        "LLM rain insight"
    )

    assert cards[0].rank == 1
    assert cards[1].rank == 2

    assert cards[0].score == 0.9
    assert cards[1].score == 0.8


@pytest.mark.asyncio
async def test_original_ml_insight_used_when_llm_returns_nothing():
    llm_service = FakeLLMInsightService(
        {}
    )

    service = object.__new__(
        PersonalizationService
    )

    service.llm_insight_service = (
        llm_service
    )

    ml_cards = [
        SimpleNamespace(
            card="temperature",
            rank=1,
            score=0.9,
            insight="Original temperature insight",
        ),
    ]

    weather = SimpleNamespace(
        model_dump=lambda **_: {
            "temperature_2m": 30.0,
        }
    )

    insights = await service._generate_llm_insights(
        ml_cards=ml_cards,
        weather=weather,
        personas=["fitness"],
    )

    cards = service._translate_ml_cards(
        ml_cards,
        llm_insights=insights,
    )

    assert cards[0].insight == (
        "Original temperature insight"
    )


@pytest.mark.asyncio
async def test_llm_disabled_keeps_ml_insights():
    service = object.__new__(
        PersonalizationService
    )

    service.llm_insight_service = None

    ml_cards = [
        SimpleNamespace(
            card="temperature",
            rank=1,
            score=0.9,
            insight="Original temperature insight",
        ),
    ]

    weather = SimpleNamespace(
        model_dump=lambda **_: {
            "temperature_2m": 30.0,
        }
    )

    insights = await service._generate_llm_insights(
        ml_cards=ml_cards,
        weather=weather,
        personas=["fitness"],
    )

    assert insights == {}

    cards = service._translate_ml_cards(
        ml_cards,
        llm_insights=insights,
    )

    assert cards[0].insight == (
        "Original temperature insight"
    )


@pytest.mark.asyncio
async def test_llm_receives_normalized_weather_and_personas():
    llm_service = FakeLLMInsightService(
        {
            "surf_conditions": "LLM surf insight",
        }
    )

    service = object.__new__(
        PersonalizationService
    )

    service.llm_insight_service = (
        llm_service
    )

    ml_cards = [
        SimpleNamespace(
            card="surf_conditions",
            rank=1,
            score=0.95,
            insight="Original surf insight",
        ),
    ]

    weather = SimpleNamespace(
        model_dump=lambda **_: {
            "wave_height": 0.8,
            "wave_period": 8.0,
            "marine_data_available": True,
        }
    )

    await service._generate_llm_insights(
        ml_cards=ml_cards,
        weather=weather,
        personas=[
            "surfer",
            "traveler",
        ],
    )

    assert len(llm_service.calls) == 1

    call = llm_service.calls[0]

    assert call["cards"] == [
        {
            "card": "surf_conditions",
            "rank": 1,
            "score": 0.95,
        }
    ]

    assert (
        call["weather_context"][
            "wave_height"
        ]
        == 0.8
    )

    assert (
        call["weather_context"][
            "wave_period"
        ]
        == 8.0
    )

    assert call["persona_context"] == {
        "personas": [
            "surfer",
            "traveler",
        ]
    }