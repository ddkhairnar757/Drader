from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pandas as pd

from .trade import Trade


@dataclass
class Portfolio:
    starting_capital: float
    commission_per_trade: float = 1.0
    slippage_pct: float = 0.0005
    cash: float = field(init=False)
    open_trade: Trade | None = field(init=False, default=None)
    closed_trades: List[Trade] = field(init=False, default_factory=list)
    equity_history: List[dict[str, float]] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.cash = self.starting_capital

    def has_open_position(self) -> bool:
        return self.open_trade is not None

    def open_position(
        self,
        entry_dt: pd.Timestamp,
        entry_price: float,
        quantity: int,
        stop_loss: float | None,
        take_profit: float | None,
    ) -> None:
        if quantity <= 0:
            return
        if self.has_open_position():
            return

        effective_entry = entry_price * (1.0 + self.slippage_pct)
        slippage_cost = entry_price * quantity * self.slippage_pct
        total_cost = effective_entry * quantity + self.commission_per_trade

        if total_cost > self.cash:
            raise ValueError("Not enough cash to open the requested position.")

        self.cash -= total_cost
        self.open_trade = Trade(
            entry_dt=entry_dt,
            entry_price=effective_entry,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            commission=self.commission_per_trade,
            slippage=slippage_cost,
        )

    def close_position(self, exit_dt: pd.Timestamp, exit_price: float) -> None:
        if not self.has_open_position() or self.open_trade is None:
            return

        effective_exit = exit_price * (1.0 - self.slippage_pct)
        slippage_cost = exit_price * self.open_trade.quantity * self.slippage_pct
        commission_cost = self.commission_per_trade

        self.open_trade.close(
            exit_dt=exit_dt,
            exit_price=effective_exit,
            commission=commission_cost,
            slippage=slippage_cost,
        )

        proceeds = effective_exit * self.open_trade.quantity - commission_cost
        self.cash += proceeds
        self.closed_trades.append(self.open_trade)
        self.open_trade = None

    def record_equity(self, current_dt: pd.Timestamp, market_price: float) -> None:
        position_value = 0.0
        if self.has_open_position() and self.open_trade is not None:
            position_value = self.open_trade.quantity * market_price

        equity = self.cash + position_value
        self.equity_history.append(
            {
                "date": current_dt,
                "cash": self.cash,
                "position_value": position_value,
                "equity": equity,
            }
        )

    def to_equity_curve(self) -> pd.DataFrame:
        return pd.DataFrame(self.equity_history).set_index("date")
