from typing import Any

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

from src.api_response import build_api_response
from src.interaction_store import save_interaction
from src.interaction_store import get_user_interactions
from typing import Literal
from fastapi import HTTPException


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title="Mausam Personalization ML API",
    version="1.0.0"
)


# ============================================================
# Request model
# ============================================================

class PersonalizationRequest(BaseModel):
    user_id: str
    weather: dict
    persona: Literal["fitness", "farmer", "traveler"]

class InteractionRequest(BaseModel):
    user_id: str
    card_id: str
    action: str
    timestamp: str
    position: int
    session_id: str


REQUIRED_WEATHER_FIELDS = [
    "city",
    "timestamp",
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "weather_code",
    "wind_speed_10m",
    "soil_moisture_0_to_7cm",
    "us_aqi",
    "european_aqi",
    "uv_index",
    "pm2_5",
    "pm10",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "carbon_monoxide",
    "ozone",
    "sunrise",
    "sunset",
    "is_daylight"
]


# ============================================================
# Health check
# ============================================================

@app.get("/")
def root():
    return {
        "service": "Mausam Personalization ML API",
        "status": "running"
    }


# ============================================================
# Personalization endpoint
# ============================================================

@app.post("/personalize")
def personalize(
    request: PersonalizationRequest
):
    missing_fields = [
        field
        for field in REQUIRED_WEATHER_FIELDS
        if field not in request.weather
    ]

    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Incomplete weather data",
                "missing_fields": missing_fields
            }
        )

    weather_data = pd.Series(
        request.weather
    )

    interactions = get_user_interactions(
        request.user_id
    )

    response = build_api_response(
        weather_data,
        request.persona,
        interactions
    )

    return response

@app.post("/interaction")
def record_interaction(
    request: InteractionRequest
):

    interaction = {
        "user_id": request.user_id,
        "card_id": request.card_id,
        "action": request.action,
        "timestamp": request.timestamp,
        "position": request.position,
        "session_id": request.session_id
    }

    save_interaction(
        interaction
    )

    return {
        "status": "success",
        "message": "Interaction recorded",
        "interaction": interaction
    }