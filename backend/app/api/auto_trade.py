from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.auto_trade import AutoTradeConfig, AutoTradeLog
from app.services.auto_trader import run_auto_trade_cycle
from app.services.execution_engine import process_pending_orders
from app.services.market_data import DummyMarketDataProvider
from app.services.scheduler import is_scheduler_running, start_scheduler, stop_scheduler

router = APIRouter(prefix="/api/auto-trade", tags=["auto-trade"])


# --- 자동매매 설정 ---


class ConfigRequest(BaseModel):
    stock_code: str
    stock_name: str = ""
    strategy_name: str
    quantity: int = 1
    max_invest_amount: float = 1_000_000


class ConfigResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: str
    strategy_name: str
    is_active: bool
    quantity: int
    max_invest_amount: float

    model_config = {"from_attributes": True}


@router.post("/configs", response_model=ConfigResponse)
def create_config(req: ConfigRequest, db: Session = Depends(get_db)):
    config = AutoTradeConfig(
        stock_code=req.stock_code,
        stock_name=req.stock_name,
        strategy_name=req.strategy_name,
        quantity=req.quantity,
        max_invest_amount=req.max_invest_amount,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("/configs", response_model=list[ConfigResponse])
def list_configs(db: Session = Depends(get_db)):
    return db.query(AutoTradeConfig).all()


@router.patch("/configs/{config_id}/toggle", response_model=ConfigResponse)
def toggle_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(AutoTradeConfig).filter_by(id=config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    config.is_active = not config.is_active
    db.commit()
    db.refresh(config)
    return config


@router.delete("/configs/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(AutoTradeConfig).filter_by(id=config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    db.delete(config)
    db.commit()
    return {"deleted": config_id}


# --- 스케줄러 제어 ---


class SchedulerStatus(BaseModel):
    running: bool


@router.get("/scheduler/status", response_model=SchedulerStatus)
def scheduler_status():
    return SchedulerStatus(running=is_scheduler_running())


@router.post("/scheduler/start", response_model=SchedulerStatus)
def scheduler_start(interval_minutes: int = 5):
    start_scheduler(interval_minutes)
    return SchedulerStatus(running=True)


@router.post("/scheduler/stop", response_model=SchedulerStatus)
def scheduler_stop():
    stop_scheduler()
    return SchedulerStatus(running=False)


@router.post("/scheduler/trigger")
def scheduler_trigger(db: Session = Depends(get_db)):
    market = DummyMarketDataProvider()
    logs = run_auto_trade_cycle(db, market)
    process_pending_orders(db, market)
    return {"triggered": True, "configs_checked": len(logs)}


# --- 실행 로그 ---


class LogResponse(BaseModel):
    id: int
    config_id: int
    stock_code: str
    strategy_name: str
    signal: str
    reason: str
    action_taken: str
    order_id: int | None
    created_at: str

    model_config = {"from_attributes": True}


@router.get("/logs", response_model=list[LogResponse])
def list_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AutoTradeLog).order_by(AutoTradeLog.created_at.desc()).limit(limit).all()
    return [
        LogResponse(
            id=log.id,
            config_id=log.config_id,
            stock_code=log.stock_code,
            strategy_name=log.strategy_name,
            signal=log.signal,
            reason=log.reason,
            action_taken=log.action_taken,
            order_id=log.order_id,
            created_at=str(log.created_at),
        )
        for log in logs
    ]
