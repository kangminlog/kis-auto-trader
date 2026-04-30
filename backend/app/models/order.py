from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(StrEnum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_code: Mapped[str] = mapped_column(String(20), ForeignKey("stocks.code"))
    side: Mapped[str] = mapped_column(String(10))  # OrderSide
    order_type: Mapped[str] = mapped_column(String(10))  # OrderType
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.PENDING)
    quantity: Mapped[int] = mapped_column()
    price: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)  # None for market order
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    executions: Mapped[list["Execution"]] = relationship(back_populates="order")  # noqa: F821
