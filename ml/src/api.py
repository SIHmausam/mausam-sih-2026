from datetime import datetime
from typing import Literal

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.api_response import build_api_response
from src.interaction_store import save_interaction
from src.interaction_store import get_user_interactions


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title="Mausam Personalization ML API",
    version="2.0.0"
)


# ============================================================
# Canonical Phase 2 types
# ============================================================

Persona = Literal[
    "health_conscious",
    "fitness",
    "surfer",
    "traveler",
    "parents_families",
    "farmer",
    "commuter",
    "event_planner"
]

CardID = Literal[
    "temperature",
    "weather_conditions",
    "humidity",
    "rain_forecast",
    "wind",
    "air_quality",
    "uv_allergy",
    "running_conditions",
    "surf_conditions",
    "tide_water",
    "farm_garden",
    "commute_conditions",
    "travel_conditions",
    "family_school",
    "event_conditions"
]


# ============================================================
# Weather request model
#
# These fields correspond to the Phase 2 raw weather contract.
# Temporal ML features (hour/day_of_week/month) are derived
# from timestamp inside the API.
# ============================================================

class WeatherFeatures(BaseModel):

    # --------------------------------------------------------
    # Context
    # --------------------------------------------------------

    city: str
    timestamp: str

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    temperature_2m: float
    relative_humidity_2m: float
    dew_point_2m: float
    apparent_temperature: float
    precipitation: float
    rain: float
    weather_code: int
    cloud_cover: float
    wind_speed_10m: float
    wind_direction_10m: float
    wind_gusts_10m: float

    # --------------------------------------------------------
    # Agriculture
    # --------------------------------------------------------

    soil_moisture_0_to_7cm: float
    soil_moisture_7_to_28cm: float
    soil_moisture_28_to_100cm: float
    soil_moisture_100_to_255cm: float

    soil_temperature_0_to_7cm: float
    soil_temperature_7_to_28cm: float
    soil_temperature_28_to_100cm: float
    soil_temperature_100_to_255cm: float

    et0_fao_evapotranspiration: float

    # --------------------------------------------------------
    # Precipitation / forecast context
    # --------------------------------------------------------

    precipitation_hours: float
    precipitation_probability: float
    showers: float
    visibility: float

    # --------------------------------------------------------
    # Air quality + UV
    # --------------------------------------------------------

    european_aqi: float
    us_aqi: float
    uv_index: float
    uv_index_clear_sky: float
    pm2_5: float
    pm10: float
    nitrogen_dioxide: float
    sulphur_dioxide: float
    carbon_monoxide: float
    ozone: float

    # --------------------------------------------------------
    # Marine
    #
    # None is valid when marine_data_available is false.
    # --------------------------------------------------------

    wave_height: float | None = None
    wave_direction: float | None = None
    wave_period: float | None = None

    swell_wave_height: float | None = None
    swell_wave_direction: float | None = None
    swell_wave_period: float | None = None

    sea_level_height_msl: float | None = None
    sea_surface_temperature: float | None = None

    marine_data_available: bool

    # --------------------------------------------------------
    # Astronomy / daylight
    # --------------------------------------------------------

    sunrise: str
    sunset: str
    is_daylight: bool


# ============================================================
# Personalization request
# ============================================================

class PersonalizationRequest(BaseModel):

    user_id: str

    personas: list[Persona] = Field(
        min_length=1,
        max_length=3
    )

    weather: WeatherFeatures


# ============================================================
# Interaction request
# ============================================================

class InteractionRequest(BaseModel):

    user_id: str

    card_id: CardID

    action: Literal[
        "view",
        "click",
        "expand",
        "dismiss"
    ]

    timestamp: str

    position: int = Field(
        ge=1,
        le=15
    )

    session_id: str


# ============================================================
# Health check
# ============================================================

@app.get("/")
def root():

    return {
        "service": "Mausam Personalization ML API",
        "status": "running",
        "version": "2.0.0"
    }


# ============================================================
# Personalization endpoint
# ============================================================

@app.post("/personalize")
def personalize(
    request: PersonalizationRequest
):

    # --------------------------------------------------------
    # Convert request to pandas Series
    # --------------------------------------------------------

    weather_data = pd.Series(
        request.weather.model_dump()
    )

    # --------------------------------------------------------
    # Derive temporal features required by Phase 2 ML model
    # --------------------------------------------------------

    try:
        timestamp = pd.to_datetime(
            request.weather.timestamp
        )
    except Exception as exc:
        raise ValueError(
            "Invalid timestamp. Expected a valid date/time string."
        ) from exc

    weather_data["hour"] = timestamp.hour
    weather_data["day_of_week"] = timestamp.dayofweek
    weather_data["month"] = timestamp.month

    # --------------------------------------------------------
    # Load behavioral interaction history
    # --------------------------------------------------------

    interactions = get_user_interactions(
        request.user_id
    )

    # --------------------------------------------------------
    # Build personalized response
    # --------------------------------------------------------

    response = build_api_response(
        weather_data,
        request.personas,
        interactions
    )

    return response


# ============================================================
# Interaction endpoint
# ============================================================

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
