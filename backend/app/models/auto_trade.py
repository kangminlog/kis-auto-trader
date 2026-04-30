from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AutoTradeConfig(Base):
    """자동매매 설정. 종목 + 전략 조합."""

    __tablename__ = "auto_trade_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_code: Mapped[str] = mapped_column(String(20))
    stock_name: Mapped[str] = mapped_column(String(100), default="")
    strategy_name: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(default=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    max_invest_amount: Mapped[float] = mapped_column(Float, default=1_000_000)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AutoTradeLog(Base):
    """자동매매 실행 로그."""

    __tablename__ = "auto_trade_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    config_id: Mapped[int] = mapped_column(Integer)
    stock_code: Mapped[str] = mapped_column(String(20))
    strategy_name: Mapped[str] = mapped_column(String(50))
    signal: Mapped[str] = mapped_column(String(10))  # buy / sell / hold
    reason: Mapped[str] = mapped_column(String(500))
    action_taken: Mapped[str] = mapped_column(String(50))  # order_placed / skipped / error
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
