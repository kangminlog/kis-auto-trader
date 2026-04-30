import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.database import SessionLocal
from app.services.auto_trader import run_auto_trade_cycle
from app.services.execution_engine import process_pending_orders
from app.services.market_data import DummyMarketDataProvider

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _auto_trade_job():
    """스케줄러가 호출하는 자동매매 작업."""
    logger.info("Auto trade cycle started at %s", datetime.now().strftime("%H:%M:%S"))
    db = SessionLocal()
    try:
        market = DummyMarketDataProvider()

        # 1. 전략 실행 → 시그널 발생 시 주문 생성
        logs = run_auto_trade_cycle(db, market)

        # 2. 생성된 주문 체결
        executions = process_pending_orders(db, market)

        buy_count = sum(1 for log in logs if log.action_taken == "order_placed" and log.signal == "buy")
        sell_count = sum(1 for log in logs if log.action_taken == "order_placed" and log.signal == "sell")
        logger.info(
            "Cycle done: %d configs checked, %d buys, %d sells, %d executions",
            len(logs),
            buy_count,
            sell_count,
            len(executions),
        )
    except Exception as e:
        logger.error("Auto trade job failed: %s", e)
    finally:
        db.close()


def start_scheduler(interval_minutes: int = 5):
    """자동매매 스케줄러 시작."""
    global _scheduler
    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_auto_trade_job, "interval", minutes=interval_minutes, id="auto_trade")
    _scheduler.start()
    logger.info("Scheduler started (interval: %d min)", interval_minutes)


def stop_scheduler():
    """자동매매 스케줄러 중지."""
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Scheduler stopped")


def is_scheduler_running() -> bool:
    return _scheduler is not None and _scheduler.running


def trigger_now():
    """즉시 한 번 실행 (테스트/수동 트리거용)."""
    _auto_trade_job()
