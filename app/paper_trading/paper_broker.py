from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    PARTIALLY_FILLED = "partially_filled"


@dataclass
class Order:
    order_id: str
    timestamp: pd.Timestamp
    symbol: str
    side: str
    quantity: int
    price: float
    filled_quantity: int = 0
    status: OrderStatus = OrderStatus.PENDING
    fill_price: float | None = None


@dataclass
class PaperPosition:
    symbol: str
    entry_price: float
    quantity: int
    entry_time: pd.Timestamp
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0


class PaperBroker:
    def __init__(
        self,
        starting_capital: float = 100_000.0,
        commission_per_trade: float = 1.0,
        slippage_pct: float = 0.0005,
    ) -> None:
        self.starting_capital = starting_capital
        self.cash = starting_capital
        self.commission_per_trade = commission_per_trade
        self.slippage_pct = slippage_pct
        self.positions: dict[str, PaperPosition] = {}
        self.orders: list[Order] = []
        self.closed_trades: list[dict[str, object]] = []

    @property
    def total_equity(self) -> float:
        unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        return self.cash + unrealized

    def update_position_values(self, current_price: float, symbol: str) -> None:
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos.unrealized_pnl = (current_price - pos.entry_price) * pos.quantity - self.commission_per_trade
            pos.unrealized_pnl_pct = (current_price - pos.entry_price) / pos.entry_price if pos.entry_price > 0 else 0.0

    def submit_order(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        current_price: float,
        timestamp: pd.Timestamp,
    ) -> Order:
        fill_price = current_price * (1.0 + self.slippage_pct) if side == "buy" else current_price * (1.0 - self.slippage_pct)
        cost = fill_price * quantity + self.commission_per_trade

        if side == "buy":
            if cost > self.cash:
                order = Order(
                    order_id=order_id,
                    timestamp=timestamp,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=current_price,
                    status=OrderStatus.CANCELLED,
                )
                self.orders.append(order)
                return order
            self.cash -= cost
            if symbol in self.positions:
                pos = self.positions[symbol]
                total_qty = pos.quantity + quantity
                total_cost = pos.entry_price * pos.quantity + fill_price * quantity
                pos.entry_price = total_cost / total_qty
                pos.quantity = total_qty
            else:
                self.positions[symbol] = PaperPosition(
                    symbol=symbol,
                    entry_price=fill_price,
                    quantity=quantity,
                    entry_time=timestamp,
                )
        elif side == "sell":
            if symbol not in self.positions or self.positions[symbol].quantity < quantity:
                order = Order(
                    order_id=order_id,
                    timestamp=timestamp,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=current_price,
                    status=OrderStatus.CANCELLED,
                )
                self.orders.append(order)
                return order

            pos = self.positions[symbol]
            proceeds = fill_price * quantity - self.commission_per_trade
            realized_pnl = (fill_price - pos.entry_price) * quantity - self.commission_per_trade
            self.cash += proceeds
            self.closed_trades.append(
                {
                    "symbol": symbol,
                    "entry_price": pos.entry_price,
                    "exit_price": fill_price,
                    "quantity": quantity,
                    "realized_pnl": realized_pnl,
                    "entry_time": pos.entry_time,
                    "exit_time": timestamp,
                }
            )
            pos.quantity -= quantity
            if pos.quantity == 0:
                del self.positions[symbol]

        order = Order(
            order_id=order_id,
            timestamp=timestamp,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=current_price,
            filled_quantity=quantity,
            status=OrderStatus.FILLED,
            fill_price=fill_price,
        )
        self.orders.append(order)
        return order
