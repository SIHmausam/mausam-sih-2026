from typing import Literal

from pydantic import BaseModel, Field

WeatherMapLayer = Literal[
    "precipitation",
    "temperature",
    "wind",
    "clouds",
]


class WeatherMapLayerResponse(BaseModel):
    id: WeatherMapLayer

    label: str

    opacity: float = Field(
        ge=0,
        le=1,
    )


class WeatherMapConfigResponse(BaseModel):
    default_layer: WeatherMapLayer

    tile_url_template: str

    min_zoom: int
    max_zoom: int

    cache_ttl_seconds: int

    attribution: str

    layers: list[WeatherMapLayerResponse]