from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import pandas as pd

from app.paper_trading.paper_broker import PaperBroker, PaperPosition


@dataclass
class PositionSnapshot:
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    entry_time: pd.Timestamp
    timestamp: pd.Timestamp


class PositionTracker:
    def __init__(self, broker: PaperBroker) -> None:
        self.broker = broker
        self.snapshots: list[PositionSnapshot] = []

    def capture_snapshot(self, current_prices: dict[str, float], timestamp: pd.Timestamp) -> None:
        for symbol, pos in self.broker.positions.items():
            current_price = current_prices.get(symbol, pos.entry_price)
            self.broker.update_position_values(current_price, symbol)
            snapshot = PositionSnapshot(
                symbol=symbol,
                quantity=pos.quantity,
                entry_price=pos.entry_price,
                current_price=current_price,
                unrealized_pnl=pos.unrealized_pnl,
                unrealized_pnl_pct=pos.unrealized_pnl_pct,
                entry_time=pos.entry_time,
                timestamp=timestamp,
            )
            self.snapshots.append(snapshot)

    def get_current_positions(self) -> list[PositionSnapshot]:
        latest_snapshots: dict[str, PositionSnapshot] = {}
        for snapshot in self.snapshots:
            latest_snapshots[snapshot.symbol] = snapshot
        return list(latest_snapshots.values())

    def get_total_unrealized_pnl(self) -> float:
        return sum(pos.unrealized_pnl for pos in self.get_current_positions())

    def get_total_exposure(self) -> float:
        return sum(pos.entry_price * pos.quantity for pos in self.get_current_positions())

    def get_exposure_ratio(self) -> float:
        total_equity = self.broker.total_equity
        return self.get_total_exposure() / total_equity if total_equity > 0 else 0.0

    def get_position_by_symbol(self, symbol: str) -> PositionSnapshot | None:
        current = self.get_current_positions()
        for snapshot in current:
            if snapshot.symbol == symbol:
                return snapshot
        return None

    def summary(self) -> dict[str, object]:
        positions = self.get_current_positions()
        return {
            "position_count": len(positions),
            "total_unrealized_pnl": self.get_total_unrealized_pnl(),
            "total_exposure": self.get_total_exposure(),
            "exposure_ratio": self.get_exposure_ratio(),
            "positions": [pos.__dict__ for pos in positions],
        }
