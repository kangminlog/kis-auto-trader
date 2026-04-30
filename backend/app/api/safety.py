from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.safety import get_daily_stats, safety

router = APIRouter(prefix="/api/safety", tags=["safety"])


class SafetyStatus(BaseModel):
    date: str
    trade_count: int
    trade_amount: float
    max_trades: int
    max_amount: float
    kill_switch: bool
    stop_loss_pct: float
    take_profit_pct: float


@router.get("/status", response_model=SafetyStatus)
def status(db: Session = Depends(get_db)):
    return get_daily_stats(db)


class KillSwitchRequest(BaseModel):
    active: bool


@router.post("/kill-switch", response_model=SafetyStatus)
def set_kill_switch(req: KillSwitchRequest, db: Session = Depends(get_db)):
    safety.kill_switch = req.active
    return get_daily_stats(db)


class SafetyConfigUpdate(BaseModel):
    daily_max_trades: int | None = None
    daily_max_amount: float | None = None
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None


@router.patch("/config", response_model=SafetyStatus)
def update_config(req: SafetyConfigUpdate, db: Session = Depends(get_db)):
    if req.daily_max_trades is not None:
        safety.daily_max_trades = req.daily_max_trades
    if req.daily_max_amount is not None:
        safety.daily_max_amount = req.daily_max_amount
    if req.stop_loss_pct is not None:
        safety.stop_loss_pct = req.stop_loss_pct
    if req.take_profit_pct is not None:
        safety.take_profit_pct = req.take_profit_pct
    return get_daily_stats(db)
