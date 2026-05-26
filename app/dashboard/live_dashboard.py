"""
Live Dashboard
==============

Unified real-time dashboard orchestrator combining all monitoring views.

Purpose: Single pane of glass for real-time strategy behavior, portfolio health,
risk metrics, signal flow, and operational state during paper trading sessions.

Design:
- Aggregates EquityMonitor, PositionPanel, SignalMonitor, SessionView
- Provides unified DashboardSnapshot for visualization/review
- Enables refresh cycles for real-time updates
- Supports behavioral flagging for review rituals
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.dashboard.equity_monitor import EquityMonitor, EquitySnapshot
from app.dashboard.position_panel import PositionPanel, PortfolioExposure
from app.dashboard.signal_monitor import SignalMonitor, SignalDistribution, SignalSide
from app.dashboard.session_view import SessionView, SessionSnapshot, MarketSessionState


@dataclass
class DashboardSnapshot:
    """Unified view of all dashboard metrics."""
    timestamp: datetime
    
    # Equity state
    equity_snapshot: EquitySnapshot
    
    # Portfolio state
    portfolio_exposure: PortfolioExposure
    
    # Signal state
    signal_distribution: SignalDistribution
    
    # Session state
    session_snapshot: SessionSnapshot
    
    # Critical flags for review ritual
    critical_review_items: List[str] = field(default_factory=list)
    operational_health_score: float = 0.0  # 0–10
    
    # Behavioral observations
    observations: List[str] = field(default_factory=list)


class LiveDashboard:
    """Real-time dashboard aggregation and monitoring."""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        
        self.equity_monitor = EquityMonitor(initial_capital)
        self.position_panel = PositionPanel(initial_capital)
        self.signal_monitor = SignalMonitor()
        self.session_view = SessionView(datetime.now().date())
        
        self.session_view.initialize_session(initial_capital)
        
        self.market_state = MarketSessionState.CLOSED
        self.last_snapshot_time: Optional[datetime] = None
        self.snapshot_history: List[DashboardSnapshot] = []
    
    def set_market_state(self, state: MarketSessionState) -> None:
        """Update market session state."""
        self.market_state = state
    
    def record_equity_update(self, current_equity: float) -> None:
        """Update equity tracking."""
        self.equity_monitor.record_equity_update(datetime.now(), current_equity)
        self.session_view.current_equity = current_equity
    
    def record_position_update(
        self,
        symbol: str,
        quantity: int,
        entry_price: float,
        current_price: float,
        entry_time: datetime,
    ) -> None:
        """Update position tracking."""
        self.position_panel.record_position_update(
            symbol, quantity, entry_price, current_price, entry_time
        )
    
    def record_signal(
        self,
        strategy_name: str,
        symbol: str,
        side: SignalSide,
        quantity: int,
        reason: str,
        executed: bool = False,
    ) -> None:
        """Record new signal."""
        self.signal_monitor.record_signal(
            strategy_name, symbol, side, quantity, reason
        )
        self.session_view.record_signal(executed)
    
    def record_signal_execution(
        self,
        symbol: str,
        filled_quantity: int,
        execution_price: float,
    ) -> None:
        """Mark signal as executed."""
        # Find most recent signal for this symbol
        signals = self.signal_monitor.get_symbol_signals(symbol)
        if signals:
            self.signal_monitor.record_execution(
                signals[-1], filled_quantity, execution_price
            )
    
    def record_trade_result(self, is_winning: bool) -> None:
        """Log trade outcome."""
        self.session_view.record_trade_result(is_winning)
    
    def get_dashboard_snapshot(self) -> DashboardSnapshot:
        """Current unified dashboard state."""
        now = datetime.now()
        
        # Collect all component snapshots
        equity_snap = self.equity_monitor.get_equity_snapshot()
        portfolio_snap = self.position_panel.get_portfolio_exposure()
        signal_snap = self.signal_monitor.get_signal_distribution()
        session_snap = self.session_view.get_session_snapshot(self.market_state)
        
        # Identify critical review items
        critical_items = self._identify_critical_items(
            equity_snap, portfolio_snap, signal_snap, session_snap
        )
        
        # Generate observations
        observations = self._generate_observations(
            equity_snap, portfolio_snap, signal_snap, session_snap
        )
        
        # Calculate health score
        health_score = self._calculate_health_score(
            equity_snap, portfolio_snap, signal_snap, session_snap
        )
        
        snapshot = DashboardSnapshot(
            timestamp=now,
            equity_snapshot=equity_snap,
            portfolio_exposure=portfolio_snap,
            signal_distribution=signal_snap,
            session_snapshot=session_snap,
            critical_review_items=critical_items,
            operational_health_score=health_score,
            observations=observations,
        )
        
        self.snapshot_history.append(snapshot)
        self.last_snapshot_time = now
        
        return snapshot
    
    def _identify_critical_items(
        self,
        equity: EquitySnapshot,
        portfolio: PortfolioExposure,
        signals: SignalDistribution,
        session: SessionSnapshot,
    ) -> List[str]:
        """Items requiring immediate review."""
        items = []
        
        # Equity red flags
        if equity.current_drawdown_pct > 5.0:
            items.append(f"Deep drawdown: {equity.current_drawdown_pct:.1f}%")
        
        if equity.multiple_clusters_flag:
            items.append(f"Multiple drawdown clusters: {len(equity.drawdown_clusters_today)}")
        
        # Portfolio red flags
        if portfolio.exposure_rating == "critical":
            items.append(f"CRITICAL LEVERAGE: {portfolio.deployment_ratio:.1%} deployed")
        
        if portfolio.largest_position_exposure_pct > 20:
            items.append(f"Concentration risk: {portfolio.largest_position_exposure_pct:.1f}%")
        
        # Signal red flags
        if signals.is_overtrading:
            items.append(f"OVERTRADING: {signals.avg_signal_frequency_per_minute:.2f} signals/min")
        
        if signals.has_contradictory_signals:
            items.append("Contradictory signals detected")
        
        # Session red flags
        if session.win_rate < 30 and session.closed_positions_today >= 3:
            items.append(f"Poor win rate: {session.win_rate:.1f}% on {session.closed_positions_today} trades")
        
        return items
    
    def _generate_observations(
        self,
        equity: EquitySnapshot,
        portfolio: PortfolioExposure,
        signals: SignalDistribution,
        session: SessionSnapshot,
    ) -> List[str]:
        """Behavioral observations for daily review."""
        obs = []
        
        # Equity observations
        if equity.smoothness_score > 0.8:
            obs.append("✓ Equity curve smooth and consistent")
        elif equity.smoothness_score < 0.5:
            obs.append("⚠ Equity curve volatile (high intraday noise)")
        
        # Portfolio observations
        if portfolio.deployment_ratio < 0.3:
            obs.append(f"Conservative: Only {portfolio.deployment_ratio:.0%} deployed")
        elif portfolio.deployment_ratio > 0.7:
            obs.append(f"Aggressive: {portfolio.deployment_ratio:.0%} of capital in use")
        
        # Signal observations
        if signals.avg_signal_frequency_per_minute > 0.5:
            obs.append(f"Frequent signaling: {signals.avg_signal_frequency_per_minute:.2f} signals/min")
        
        if signals.execution_rate > 0.9:
            obs.append(f"High execution fidelity: {signals.execution_rate:.0%} executed")
        elif signals.execution_rate < 0.5:
            obs.append(f"Low execution rate: {signals.execution_rate:.0%} actually executed")
        
        # Trade quality observations
        if session.win_rate > 60:
            obs.append(f"✓ Strong trade quality: {session.win_rate:.0f}% win rate")
        elif session.win_rate < 40 and session.closed_positions_today > 0:
            obs.append(f"⚠ Below-average win rate: {session.win_rate:.0f}%")
        
        return obs
    
    def _calculate_health_score(
        self,
        equity: EquitySnapshot,
        portfolio: PortfolioExposure,
        signals: SignalDistribution,
        session: SessionSnapshot,
    ) -> float:
        """Overall operational health (0–10)."""
        score = 10.0
        
        # Equity health (0–3 points)
        if equity.current_drawdown_pct > 10:
            score -= 2.0
        elif equity.current_drawdown_pct > 5:
            score -= 1.0
        
        if equity.smoothness_score < 0.5:
            score -= 0.5
        
        # Portfolio health (0–3 points)
        if portfolio.exposure_rating == "critical":
            score -= 2.5
        elif portfolio.exposure_rating == "warning":
            score -= 1.0
        
        # Signal health (0–2 points)
        if signals.is_overtrading:
            score -= 1.5
        
        if signals.has_contradictory_signals:
            score -= 0.5
        
        # Session health (0–2 points)
        if session.closed_positions_today > 0 and session.win_rate < 30:
            score -= 1.5
        
        return max(0, min(10, score))
    
    def get_health_rating(self) -> str:
        """Overall operational rating."""
        snapshot = self.get_dashboard_snapshot()
        score = snapshot.operational_health_score
        
        if score >= 8:
            return "EXCELLENT"
        elif score >= 6:
            return "GOOD"
        elif score >= 4:
            return "FAIR"
        elif score >= 2:
            return "POOR"
        else:
            return "CRITICAL"
    
    def print_dashboard(self) -> str:
        """Formatted dashboard output."""
        snapshot = self.get_dashboard_snapshot()
        
        lines = [
            f"\n{'='*70}",
            f"LIVE DASHBOARD - {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*70}",
            f"\n--- EQUITY MONITOR ---",
            f"Opening: ${snapshot.equity_snapshot.opening_equity:,.2f}",
            f"Current: ${snapshot.equity_snapshot.current_equity:,.2f}",
            f"P&L: ${snapshot.equity_snapshot.session_pnl:,.2f} ({snapshot.equity_snapshot.session_return_pct:.2f}%)",
            f"Max Drawdown: {snapshot.equity_snapshot.max_drawdown_pct:.2f}%",
            f"Current Drawdown: {snapshot.equity_snapshot.current_drawdown_pct:.2f}%",
            f"Smoothness: {snapshot.equity_snapshot.smoothness_score:.2f}/1.0",
            
            f"\n--- PORTFOLIO ---",
            f"Deployed: ${snapshot.portfolio_exposure.deployed_capital:,.2f} ({snapshot.portfolio_exposure.deployment_ratio:.0%})",
            f"Open Positions: {snapshot.portfolio_exposure.open_positions_count}",
            f"Largest Position: {snapshot.portfolio_exposure.largest_position_exposure_pct:.1f}%",
            f"Status: {snapshot.portfolio_exposure.exposure_rating.upper()}",
            
            f"\n--- SIGNALS ---",
            f"Generated: {snapshot.signal_distribution.total_signals}",
            f"Executed: {snapshot.signal_distribution.total_signals - snapshot.signal_distribution.cancelled_signals}",
            f"Execution Rate: {snapshot.signal_distribution.execution_rate:.1%}",
            f"Buy/Sell Ratio: {snapshot.signal_distribution.buy_sell_ratio:.2f}",
            
            f"\n--- SESSION ---",
            f"Progress: {snapshot.session_snapshot.session_progress_pct:.0f}% (closes in {snapshot.session_snapshot.minutes_until_close:.0f}m)",
            f"Trades Closed: {snapshot.session_snapshot.closed_positions_today}",
            f"Win Rate: {snapshot.session_snapshot.win_rate:.1f}%",
            
            f"\n--- HEALTH ---",
            f"Operational Score: {snapshot.operational_health_score:.1f}/10 ({self.get_health_rating()})",
        ]
        
        if snapshot.critical_review_items:
            lines.append(f"\n--- CRITICAL ITEMS (REVIEW) ---")
            for item in snapshot.critical_review_items:
                lines.append(f"🔴 {item}")
        
        if snapshot.observations:
            lines.append(f"\n--- OBSERVATIONS ---")
            for obs in snapshot.observations:
                lines.append(f"  {obs}")
        
        lines.append(f"\n{'='*70}\n")
        
        return "\n".join(lines)
    
    def end_of_day_summary(self) -> str:
        """Generate daily review ritual summary."""
        session_summary = self.session_view.generate_end_of_day_summary()
        dashboard_health = self.print_dashboard()
        
        return f"\n{session_summary}\n{dashboard_health}"
