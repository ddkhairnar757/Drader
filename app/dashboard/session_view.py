"""
Session View
============

Real-time market session state tracking and daily metrics consolidation.

Purpose: Provide single-screen visibility into current session state, time remaining,
and consolidated daily operational metrics for end-of-day review ritual.

Design:
- Tracks market session state (CLOSED, PRE_OPEN, OPEN, CLOSE)
- Shows time until market close
- Consolidates daily journal metrics
- Summarizes execution quality and behavioral observations
"""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import List, Optional
from enum import Enum


class MarketSessionState(Enum):
    """Market session lifecycle."""
    CLOSED = "closed"           # Market closed
    PRE_OPEN = "pre_open"       # Pre-market (before 9:15)
    OPEN = "open"               # Regular trading (9:15–15:30)
    CLOSE = "close"             # Close auction (15:30+)


@dataclass
class SessionSnapshot:
    """Point-in-time session state."""
    session_date: datetime.date
    current_time: datetime
    market_state: MarketSessionState
    
    # Session timing
    session_start_time: time
    session_end_time: time
    minutes_elapsed: float
    minutes_until_close: float
    session_progress_pct: float  # 0–100%
    
    # Session metrics
    starting_equity: float
    current_equity: float
    session_pnl: float
    session_return_pct: float
    
    # Activity metrics
    signals_generated: int
    signals_executed: int
    execution_rate: float
    
    open_positions: int
    closed_positions_today: int
    
    # Quality metrics
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Operational flags
    has_quality_issues: List[str] = field(default_factory=list)  # Signal clustering, overtrading, etc.
    is_active_trading: bool = False
    is_critical_leverage: bool = False
    
    # Daily notes (for review ritual)
    daily_notes: List[str] = field(default_factory=list)


class SessionView:
    """Real-time session management and daily metrics."""
    
    def __init__(self, session_date: datetime.date):
        self.session_date = session_date
        self.session_start_time = time(9, 15)  # Asia/Kolkata market open
        self.session_end_time = time(15, 30)   # Asia/Kolkata market close
        
        self.starting_equity = 0.0
        self.current_equity = 0.0
        
        self.signals_generated = 0
        self.signals_executed = 0
        self.closed_positions_today = 0
        self.open_positions_today = 0
        
        self.winning_trades = 0
        self.losing_trades = 0
        
        self.daily_notes: List[str] = []
        self.quality_issues: List[str] = []
    
    def initialize_session(self, starting_equity: float) -> None:
        """Mark session start."""
        self.starting_equity = starting_equity
        self.current_equity = starting_equity
    
    def update_session_state(
        self,
        current_equity: float,
        open_positions: int,
        market_state: MarketSessionState,
    ) -> None:
        """Update session metrics."""
        self.current_equity = current_equity
        self.open_positions_today = open_positions
    
    def record_signal(self, executed: bool = False) -> None:
        """Track signal generation."""
        self.signals_generated += 1
        if executed:
            self.signals_executed += 1
    
    def record_trade_result(self, is_winning: bool) -> None:
        """Track trade outcome."""
        if is_winning:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        self.closed_positions_today += 1
    
    def get_session_snapshot(self, market_state: MarketSessionState) -> SessionSnapshot:
        """Current session state."""
        current_time = datetime.now()
        
        # Calculate session timing
        today = current_time.date()
        session_start = datetime.combine(today, self.session_start_time)
        session_end = datetime.combine(today, self.session_end_time)
        
        current_dt = current_time
        
        elapsed = (current_dt - session_start).total_seconds() / 60
        total_session_minutes = (session_end - session_start).total_seconds() / 60
        minutes_until_close = (session_end - current_dt).total_seconds() / 60
        
        elapsed = max(0, elapsed)
        minutes_until_close = max(0, minutes_until_close)
        progress = (elapsed / total_session_minutes * 100) if total_session_minutes > 0 else 0
        
        # Calculate P&L
        session_pnl = self.current_equity - self.starting_equity
        session_return = (session_pnl / self.starting_equity * 100) if self.starting_equity > 0 else 0
        
        # Calculate win rate
        total_trades = self.winning_trades + self.losing_trades
        win_rate = (self.winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Execution rate
        execution_rate = (self.signals_executed / self.signals_generated) if self.signals_generated > 0 else 0
        
        return SessionSnapshot(
            session_date=today,
            current_time=current_dt,
            market_state=market_state,
            session_start_time=self.session_start_time,
            session_end_time=self.session_end_time,
            minutes_elapsed=elapsed,
            minutes_until_close=minutes_until_close,
            session_progress_pct=progress,
            starting_equity=self.starting_equity,
            current_equity=self.current_equity,
            session_pnl=session_pnl,
            session_return_pct=session_return,
            signals_generated=self.signals_generated,
            signals_executed=self.signals_executed,
            execution_rate=execution_rate,
            open_positions=self.open_positions_today,
            closed_positions_today=self.closed_positions_today,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            win_rate=win_rate,
            has_quality_issues=self.quality_issues.copy(),
            daily_notes=self.daily_notes.copy(),
        )
    
    def add_daily_note(self, note: str) -> None:
        """Record observation for end-of-day review."""
        self.daily_notes.append(f"[{datetime.now().strftime('%H:%M:%S')}] {note}")
    
    def flag_quality_issue(self, issue: str) -> None:
        """Record operational concern."""
        if issue not in self.quality_issues:
            self.quality_issues.append(issue)
    
    def generate_end_of_day_summary(self) -> str:
        """Daily review ritual output."""
        snapshot = self.get_session_snapshot(MarketSessionState.CLOSED)
        
        summary_lines = [
            f"\n{'='*60}",
            f"DAILY SESSION REVIEW - {snapshot.session_date}",
            f"{'='*60}",
            f"\n--- Session Timing ---",
            f"Session: {snapshot.session_start_time} to {snapshot.session_end_time}",
            f"Duration: {snapshot.minutes_elapsed:.0f} minutes",
            f"\n--- Profitability ---",
            f"Starting Equity: ${snapshot.starting_equity:,.2f}",
            f"Ending Equity: ${snapshot.current_equity:,.2f}",
            f"Daily P&L: ${snapshot.session_pnl:,.2f}",
            f"Daily Return: {snapshot.session_return_pct:.2f}%",
            f"\n--- Activity ---",
            f"Signals Generated: {snapshot.signals_generated}",
            f"Signals Executed: {snapshot.signals_executed}",
            f"Execution Rate: {snapshot.execution_rate:.1%}",
            f"Open Positions at Close: {snapshot.open_positions}",
            f"Closed Trades Today: {snapshot.closed_positions_today}",
            f"\n--- Trade Quality ---",
            f"Winning Trades: {snapshot.winning_trades}",
            f"Losing Trades: {snapshot.losing_trades}",
            f"Win Rate: {snapshot.win_rate:.1f}%",
        ]
        
        if snapshot.has_quality_issues:
            summary_lines.append(f"\n--- Quality Issues (FOR REVIEW) ---")
            for issue in snapshot.has_quality_issues:
                summary_lines.append(f"⚠ {issue}")
        
        if snapshot.daily_notes:
            summary_lines.append(f"\n--- Daily Observations ---")
            for note in snapshot.daily_notes[-10:]:  # Last 10 notes
                summary_lines.append(f"  {note}")
        
        summary_lines.append(f"\n{'='*60}\n")
        
        return "\n".join(summary_lines)
    
    def is_market_open(self) -> bool:
        """Check if market is currently open."""
        current_time = datetime.now().time()
        return self.session_start_time <= current_time <= self.session_end_time
    
    def time_to_market_close(self) -> timedelta:
        """Time remaining until market close."""
        current_time = datetime.now().time()
        close_dt = datetime.combine(datetime.now().date(), self.session_end_time)
        current_dt = datetime.combine(datetime.now().date(), current_time)
        
        time_left = close_dt - current_dt
        return time_left
