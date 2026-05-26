from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from enum import Enum

import pandas as pd


class SessionState(str, Enum):
    CLOSED = "closed"
    PRE_OPEN = "pre_open"
    OPEN = "open"
    CLOSE = "close"


@dataclass
class SessionConfig:
    market_open_time: time = time(9, 15)
    market_close_time: time = time(15, 30)
    timezone_str: str = "Asia/Kolkata"


class SessionManager:
    def __init__(self, config: SessionConfig | None = None) -> None:
        self.config = config or SessionConfig()
        self.current_session_start: datetime | None = None
        self.current_session_end: datetime | None = None
        self.state = SessionState.CLOSED
        self.daily_pnl = 0.0
        self.session_history: list[dict[str, object]] = []

    def update_session_state(self, current_time: datetime) -> SessionState:
        current_date = current_time.date()
        open_time = datetime.combine(current_date, self.config.market_open_time, tzinfo=timezone.utc)
        close_time = datetime.combine(current_date, self.config.market_close_time, tzinfo=timezone.utc)

        if current_time < open_time:
            self.state = SessionState.CLOSED
        elif open_time <= current_time <= close_time:
            if self.state == SessionState.CLOSED or self.state == SessionState.PRE_OPEN:
                self.current_session_start = current_time
            self.state = SessionState.OPEN
        else:
            if self.state == SessionState.OPEN:
                self.current_session_end = current_time
                self.state = SessionState.CLOSE
            else:
                self.state = SessionState.CLOSED

        return self.state

    def is_market_open(self, current_time: datetime) -> bool:
        self.update_session_state(current_time)
        return self.state == SessionState.OPEN

    def get_market_open_time(self, date: datetime) -> datetime:
        return datetime.combine(date.date(), self.config.market_open_time, tzinfo=timezone.utc)

    def get_market_close_time(self, date: datetime) -> datetime:
        return datetime.combine(date.date(), self.config.market_close_time, tzinfo=timezone.utc)

    def record_session_end(self, daily_pnl: float) -> None:
        if self.current_session_start and self.current_session_end:
            self.session_history.append(
                {
                    "session_start": self.current_session_start.isoformat(),
                    "session_end": self.current_session_end.isoformat(),
                    "daily_pnl": daily_pnl,
                    "duration": (self.current_session_end - self.current_session_start).total_seconds(),
                }
            )
            self.daily_pnl = daily_pnl

    def get_session_summary(self) -> dict[str, object]:
        return {
            "current_state": self.state.value,
            "session_start": self.current_session_start.isoformat() if self.current_session_start else None,
            "session_end": self.current_session_end.isoformat() if self.current_session_end else None,
            "daily_pnl": self.daily_pnl,
            "session_count": len(self.session_history),
            "sessions": self.session_history[-5:],
        }
