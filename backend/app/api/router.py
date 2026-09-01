from fastapi import APIRouter

from app.api.routes.air_quality import (
    router as air_quality_router,
)
from app.api.routes.alerts import (
    router as alerts_router,
)
from app.api.routes.auth import router as auth_router
from app.api.routes.interactions import router as interactions_router
from app.api.routes.locations import router as locations_router
from app.api.routes.routines import (
    router as routines_router,
)
from app.api.routes.users import router as users_router
from app.api.routes.weather import router as weather_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(locations_router)
api_router.include_router(weather_router)
api_router.include_router(air_quality_router)
api_router.include_router(alerts_router)
api_router.include_router(routines_router)
api_router.include_router(interactions_router)
