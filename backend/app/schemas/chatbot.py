from pydantic import BaseModel, Field


class ChatbotRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        max_length=100,
    )
    question: str = Field(
        min_length=1,
        max_length=1000,
    )
    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )
    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )


class ChatbotResponse(BaseModel):
    answer: str
