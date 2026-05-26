from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class BacktestSettings:
    starting_capital: float = 100_000.0
    commission_per_trade: float = 1.0
    slippage_pct: float = 0.0005
    risk_per_trade: float = 0.01
    max_position_size: int = 100

    @classmethod
    def from_env(cls) -> "BacktestSettings":
        return cls(
            starting_capital=float(os.getenv("STARTING_CAPITAL", "100000.0")),
            commission_per_trade=float(os.getenv("COMMISSION_PER_TRADE", "1.0")),
            slippage_pct=float(os.getenv("SLIPPAGE_PCT", "0.0005")),
            risk_per_trade=float(os.getenv("RISK_PER_TRADE", "0.01")),
            max_position_size=int(os.getenv("MAX_POSITION_SIZE", "100")),
        )
