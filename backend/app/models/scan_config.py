from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ScanConfig(Base):
    """전략 파라미터 key-value 저장소. scan_config 테이블."""

    __tablename__ = "scan_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(String(500), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SignalOutcome(Base):
    """전략 시그널 결과 기록. 동적 파라미터 튜닝 데이터."""

    __tablename__ = "signal_outcomes"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_code: Mapped[str] = mapped_column(String(20), index=True)
    strategy_name: Mapped[str] = mapped_column(String(50))
    signal: Mapped[str] = mapped_column(String(10))  # buy / sell
    entry_price: Mapped[float] = mapped_column(Float)
    tp_price: Mapped[float] = mapped_column(Float, default=0)
    sl_price: Mapped[float] = mapped_column(Float, default=0)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)  # win / loss / open
    pnl_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    regime: Mapped[str] = mapped_column(String(10), default="side")
    params_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
