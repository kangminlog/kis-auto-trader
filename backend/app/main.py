from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.auto_trade import router as auto_trade_router
from app.api.health import router as health_router
from app.api.safety import router as safety_router
from app.api.scan_config import router as scan_config_router
from app.api.strategy import router as strategy_router
from app.api.trading import router as trading_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging("DEBUG" if settings.debug else "INFO")
    if settings.scheduler_auto_start:
        start_scheduler(settings.scheduler_interval_minutes)
    yield
    stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 공개 엔드포인트
app.include_router(health_router)
app.include_router(auth_router)

# 인증 필요 엔드포인트
app.include_router(trading_router)
app.include_router(strategy_router)
app.include_router(auto_trade_router)
app.include_router(safety_router)
app.include_router(scan_config_router)
