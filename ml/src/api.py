from typing import Any

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

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
class WeatherFeatures(BaseModel):
    city: str
    timestamp: str
    temperature_2m: float
    relative_humidity_2m: float
    apparent_temperature: float
    precipitation: float
    rain: float
    weather_code: int
    wind_speed_10m: float
    soil_moisture_0_to_7cm: float
    us_aqi: float
    european_aqi: float
    uv_index: float
    pm2_5: float
    pm10: float
    nitrogen_dioxide: float
    sulphur_dioxide: float
    carbon_monoxide: float
    ozone: float
    is_daylight: bool

class PersonalizationRequest(BaseModel):
    user_id: str
    weather: WeatherFeatures
    persona: Literal["fitness", "farmer", "traveler"]

class InteractionRequest(BaseModel):
    user_id: str
    card_id: Literal[
        "aqi",
        "uv",
        "temperature",
        "humidity",
        "rain",
        "wind",
        "soil_moisture",
        "weather_condition"
    ]
    action: Literal[
        "view",
        "click",
        "expand",
        "dismiss"
    ]
    timestamp: str
    position: int = Field(ge=1, le=8)
    session_id: str




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
    
    weather_data = pd.Series(
        request.weather.model_dump()
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