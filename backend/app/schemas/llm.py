from pydantic import BaseModel, Field


class LLMInsight(BaseModel):
    card: str
    insight: str = Field(
        min_length=1,
        max_length=300,
    )


class LLMInsightResponse(BaseModel):
    insights: list[LLMInsight]