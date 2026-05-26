from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

import pandas as pd

from app.paper_trading.paper_broker import PaperBroker


@dataclass
class SignalEvent:
    signal_id: str
    strategy_name: str
    symbol: str
    side: str
    quantity: int
    signal_price: float
    timestamp: pd.Timestamp
    reason: str | None = None


@dataclass
class ExecutionEvent:
    execution_id: str
    signal_id: str
    symbol: str
    side: str
    quantity: int
    executed_price: float
    timestamp: pd.Timestamp
    status: str = "executed"


class SignalRouter:
    def __init__(self, broker: PaperBroker) -> None:
        self.broker = broker
        self.signals: list[SignalEvent] = []
        self.executions: list[ExecutionEvent] = []
        self.hooks: list[Callable[[SignalEvent], None]] = []

    def register_hook(self, callback: Callable[[SignalEvent], None]) -> None:
        self.hooks.append(callback)

    def emit_signal(
        self,
        strategy_name: str,
        symbol: str,
        side: str,
        quantity: int,
        signal_price: float,
        timestamp: pd.Timestamp,
        reason: str | None = None,
    ) -> SignalEvent:
        signal = SignalEvent(
            signal_id=f"SIG-{uuid4().hex[:8]}",
            strategy_name=strategy_name,
            symbol=symbol,
            side=side,
            quantity=quantity,
            signal_price=signal_price,
            timestamp=timestamp,
            reason=reason,
        )
        self.signals.append(signal)
        for hook in self.hooks:
            hook(signal)
        return signal

    def execute_signal(
        self,
        signal: SignalEvent,
        current_price: float,
    ) -> ExecutionEvent | None:
        order = self.broker.submit_order(
            order_id=f"ORD-{uuid4().hex[:8]}",
            symbol=signal.symbol,
            side=signal.side,
            quantity=signal.quantity,
            current_price=current_price,
            timestamp=signal.timestamp,
        )

        if order.status.value == "filled":
            execution = ExecutionEvent(
                execution_id=f"EXE-{uuid4().hex[:8]}",
                signal_id=signal.signal_id,
                symbol=signal.symbol,
                side=signal.side,
                quantity=signal.quantity,
                executed_price=order.fill_price or current_price,
                timestamp=signal.timestamp,
                status="executed",
            )
            self.executions.append(execution)
            return execution
        else:
            return None

    def get_signal_history(self, strategy_name: str | None = None) -> list[SignalEvent]:
        if strategy_name:
            return [sig for sig in self.signals if sig.strategy_name == strategy_name]
        return self.signals

    def get_execution_history(self) -> list[ExecutionEvent]:
        return self.executions

    def summary(self) -> dict[str, object]:
        total_signals = len(self.signals)
        executed_signals = len(self.executions)
        execution_rate = executed_signals / total_signals if total_signals > 0 else 0.0
        return {
            "total_signals": total_signals,
            "executed_signals": executed_signals,
            "execution_rate": execution_rate,
            "signals": [sig.__dict__ for sig in self.signals[-10:]],
            "executions": [exe.__dict__ for exe in self.executions[-10:]],
        }
