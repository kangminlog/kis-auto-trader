from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.trading import router as trading_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(health_router)
app.include_router(trading_router)
