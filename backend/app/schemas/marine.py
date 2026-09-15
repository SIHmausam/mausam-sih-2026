from datetime import datetime

from pydantic import BaseModel


class CurrentMarineResponse(BaseModel):
    latitude: float
    longitude: float

    observed_at: datetime | None = None

    wave_height: float | None = None
    wave_direction: float | None = None
    wave_period: float | None = None

    swell_wave_height: float | None = None
    swell_wave_direction: float | None = None
    swell_wave_period: float | None = None

    sea_level_height_msl: float | None = None

    sea_surface_temperature: (
        float | None
    ) = None

    available: bool = False