"""
Dashboard Module
================

Real-time visibility layer for strategy behavior, portfolio movement, risk evolution, signal flow.

Without the dashboard, operations remain blind.
Enables daily review rituals: bad trades, overtrading, false signals, drawdown clusters, regime mismatch.

Core Components:
- EquityMonitor: Real-time equity curve, drawdown tracking, drawdown clustering
- PositionPanel: Current positions, unrealized P&L, exposure management
- SignalMonitor: Signal generation events, execution flow, signal statistics
- SessionView: Market session state, time tracking, daily metrics consolidation
- LiveDashboard: Unified orchestrator for all dashboard views

Integration Points:
- paper_trading.paper_broker: Executions and fills
- paper_trading.position_tracker: Position snapshots
- paper_trading.signal_router: Signal events
- paper_trading.session_manager: Market state
- paper_trading.daily_journal: Session metrics
- backtesting.metrics: Performance calculations
"""

from app.dashboard.equity_monitor import (
    EquityMonitor,
    EquitySnapshot,
    DrawdownCluster,
)
from app.dashboard.position_panel import (
    PositionPanel,
    PositionStatus,
    ExposureWarning,
)
from app.dashboard.signal_monitor import (
    SignalMonitor,
    SignalEvent,
    SignalDistribution,
    SignalSide,
)
from app.dashboard.session_view import (
    SessionView,
    SessionSnapshot,
    MarketSessionState,
)
from app.dashboard.live_dashboard import (
    LiveDashboard,
    DashboardSnapshot,
)

__all__ = [
    "EquityMonitor",
    "EquitySnapshot",
    "DrawdownCluster",
    "PositionPanel",
    "PositionStatus",
    "ExposureWarning",
    "SignalMonitor",
    "SignalEvent",
    "SignalDistribution",
    "SignalSide",
    "SessionView",
    "SessionSnapshot",
    "MarketSessionState",
    "LiveDashboard",
    "DashboardSnapshot",
]
