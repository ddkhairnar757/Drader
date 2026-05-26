from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Trade:
    entry_dt: pd.Timestamp
    entry_price: float
    quantity: int
    direction: str = "long"
    stop_loss: float | None = None
    take_profit: float | None = None
    commission: float = 0.0
    slippage: float = 0.0
    exit_dt: pd.Timestamp | None = None
    exit_price: float | None = None
    realized_pnl: float | None = None

    def close(
        self,
        exit_dt: pd.Timestamp,
        exit_price: float,
        commission: float,
        slippage: float,
    ) -> None:
        self.exit_dt = exit_dt
        self.exit_price = exit_price
        self.commission += commission
        self.slippage += slippage
        self.realized_pnl = self._compute_realized_pnl()

    def _compute_realized_pnl(self) -> float:
        if self.exit_price is None:
            raise ValueError("Trade must have an exit price before computing PnL.")

        gross = (self.exit_price - self.entry_price) * self.quantity
        return gross - self.commission - self.slippage
