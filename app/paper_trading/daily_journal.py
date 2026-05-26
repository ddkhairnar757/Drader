from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

from app.paper_trading.paper_broker import PaperBroker
from app.paper_trading.position_tracker import PositionTracker
from app.paper_trading.signal_router import SignalRouter


@dataclass
class DailyJournalEntry:
    session_date: datetime
    session_start: datetime
    session_end: datetime
    starting_equity: float
    ending_equity: float
    daily_pnl: float
    daily_return_pct: float
    signals_count: int
    executions_count: int
    execution_rate: float
    open_positions_count: int
    closed_trades_count: int
    max_unrealized_loss: float
    max_unrealized_gain: float
    notes: list[str]


class DailyJournal:
    def __init__(self) -> None:
        self.entries: list[DailyJournalEntry] = []

    def record_session(
        self,
        session_date: datetime,
        session_start: datetime,
        session_end: datetime,
        broker: PaperBroker,
        position_tracker: PositionTracker,
        signal_router: SignalRouter,
        starting_equity: float,
    ) -> DailyJournalEntry:
        ending_equity = broker.total_equity
        daily_pnl = ending_equity - starting_equity
        daily_return_pct = (daily_pnl / starting_equity * 100.0) if starting_equity > 0 else 0.0

        signals = signal_router.get_signal_history()
        executions = signal_router.get_execution_history()
        signals_count = len(signals)
        executions_count = len(executions)
        execution_rate = executions_count / signals_count if signals_count > 0 else 0.0

        positions = position_tracker.get_current_positions()
        open_positions_count = len(positions)
        closed_trades_count = len(broker.closed_trades)

        unrealized_losses = [pos.unrealized_pnl for pos in positions if pos.unrealized_pnl < 0]
        max_unrealized_loss = float(min(unrealized_losses)) if unrealized_losses else 0.0

        unrealized_gains = [pos.unrealized_pnl for pos in positions if pos.unrealized_pnl > 0]
        max_unrealized_gain = float(max(unrealized_gains)) if unrealized_gains else 0.0

        notes: list[str] = []
        if daily_pnl > 0:
            notes.append(f"Profitable session: {daily_pnl:.2f} ({daily_return_pct:.2f}%)")
        elif daily_pnl < 0:
            notes.append(f"Loss session: {daily_pnl:.2f} ({daily_return_pct:.2f}%)")
        else:
            notes.append("Breakeven session")

        if execution_rate < 0.5:
            notes.append(f"Low execution rate: {execution_rate:.2%}")
        if open_positions_count > 5:
            notes.append(f"High position count: {open_positions_count}")
        if max_unrealized_loss < -0.05:
            notes.append(f"Significant unrealized loss: {max_unrealized_loss:.2%}")

        entry = DailyJournalEntry(
            session_date=session_date,
            session_start=session_start,
            session_end=session_end,
            starting_equity=starting_equity,
            ending_equity=ending_equity,
            daily_pnl=daily_pnl,
            daily_return_pct=daily_return_pct,
            signals_count=signals_count,
            executions_count=executions_count,
            execution_rate=execution_rate,
            open_positions_count=open_positions_count,
            closed_trades_count=closed_trades_count,
            max_unrealized_loss=max_unrealized_loss,
            max_unrealized_gain=max_unrealized_gain,
            notes=notes,
        )
        self.entries.append(entry)
        return entry

    def get_recent_entries(self, limit: int = 10) -> list[DailyJournalEntry]:
        return self.entries[-limit:]

    def get_summary(self) -> dict[str, object]:
        if not self.entries:
            return {
                "total_sessions": 0,
                "avg_daily_pnl": 0.0,
                "winning_sessions": 0,
                "losing_sessions": 0,
                "breakeven_sessions": 0,
                "entries": [],
            }

        total_pnl = sum(entry.daily_pnl for entry in self.entries)
        winning = sum(1 for entry in self.entries if entry.daily_pnl > 0)
        losing = sum(1 for entry in self.entries if entry.daily_pnl < 0)
        breakeven = sum(1 for entry in self.entries if entry.daily_pnl == 0.0)
        avg_pnl = total_pnl / len(self.entries)

        return {
            "total_sessions": len(self.entries),
            "avg_daily_pnl": avg_pnl,
            "total_pnl": total_pnl,
            "winning_sessions": winning,
            "losing_sessions": losing,
            "breakeven_sessions": breakeven,
            "win_rate": winning / len(self.entries) if self.entries else 0.0,
            "entries": [
                {
                    "session_date": entry.session_date.isoformat(),
                    "daily_pnl": entry.daily_pnl,
                    "daily_return_pct": entry.daily_return_pct,
                    "notes": entry.notes,
                }
                for entry in self.entries[-10:]
            ],
        }
