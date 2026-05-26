"""
Equity Monitor
==============

Real-time equity curve tracking, drawdown detection, drawdown cluster analysis.

Purpose: Enable observation of portfolio smoothness, capital preservation patterns, 
and recovery behavior under live conditions.

Design:
- Tracks equity history with timestamps
- Calculates real-time max drawdown and current drawdown
- Identifies drawdown clusters (consecutive down periods)
- Flags equity volatility and smoothness degradation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
import statistics


@dataclass
class DrawdownCluster:
    """Consecutive drawdown period."""
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    max_drawdown_pct: float
    recovery_time_minutes: Optional[float]  # None if not recovered yet


@dataclass
class EquitySnapshot:
    """Point-in-time equity state."""
    timestamp: datetime
    opening_equity: float
    current_equity: float
    session_pnl: float
    session_return_pct: float
    
    # Drawdown metrics
    max_drawdown_pct: float
    current_drawdown_pct: float
    peak_equity: float
    
    # Equity quality
    equity_volatility: float  # % std dev of intraday returns
    smoothness_score: float  # 0–1, inverse of volatility
    
    # Drawdown clusters
    active_drawdown_cluster: Optional[DrawdownCluster] = None
    drawdown_clusters_today: List[DrawdownCluster] = field(default_factory=list)
    
    # Flags for review
    is_in_drawdown: bool = False
    multiple_clusters_flag: bool = False  # More than 2 clusters = concerning


class EquityMonitor:
    """Real-time equity tracking and analysis."""
    
    def __init__(self, opening_equity: float):
        """
        Args:
            opening_equity: Starting capital at session open
        """
        self.opening_equity = opening_equity
        self.equity_history: List[tuple[datetime, float]] = [
            (datetime.now(), opening_equity)
        ]
        self.drawdown_clusters: List[DrawdownCluster] = []
        
    def record_equity_update(self, timestamp: datetime, current_equity: float) -> None:
        """Record equity tick."""
        self.equity_history.append((timestamp, current_equity))
    
    def get_equity_snapshot(self) -> EquitySnapshot:
        """Current equity state with all calculated metrics."""
        if not self.equity_history:
            raise ValueError("No equity history recorded")
        
        current_time, current_equity = self.equity_history[-1]
        opening_time, opening_equity = self.equity_history[0]
        
        # Calculate session metrics
        session_pnl = current_equity - opening_equity
        session_return_pct = (session_pnl / opening_equity) * 100 if opening_equity > 0 else 0
        
        # Calculate max drawdown and current drawdown
        peak_equity = opening_equity
        max_dd = 0
        current_dd = 0
        is_in_drawdown = False
        
        for _, equity in self.equity_history:
            peak_equity = max(peak_equity, equity)
            dd = ((peak_equity - equity) / peak_equity) * 100 if peak_equity > 0 else 0
            max_dd = max(max_dd, dd)
            if equity == current_equity:
                current_dd = dd
                is_in_drawdown = (dd > 0.01)
        
        # Calculate equity volatility
        equity_volatility = self._calculate_equity_volatility()
        smoothness_score = max(0, 1 - (equity_volatility / 100)) if equity_volatility > 0 else 1.0
        
        # Identify active drawdown cluster
        active_cluster = self._identify_active_drawdown_cluster(current_time)
        
        # Count clusters
        multiple_clusters_flag = len(self.drawdown_clusters) > 2
        
        return EquitySnapshot(
            timestamp=current_time,
            opening_equity=opening_equity,
            current_equity=current_equity,
            session_pnl=session_pnl,
            session_return_pct=session_return_pct,
            max_drawdown_pct=max_dd,
            current_drawdown_pct=current_dd,
            peak_equity=peak_equity,
            equity_volatility=equity_volatility,
            smoothness_score=smoothness_score,
            active_drawdown_cluster=active_cluster,
            drawdown_clusters_today=self.drawdown_clusters.copy(),
            is_in_drawdown=is_in_drawdown,
            multiple_clusters_flag=multiple_clusters_flag,
        )
    
    def _calculate_equity_volatility(self) -> float:
        """Intraday equity volatility (% std dev)."""
        if len(self.equity_history) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(self.equity_history)):
            prev_equity = self.equity_history[i-1][1]
            curr_equity = self.equity_history[i][1]
            if prev_equity > 0:
                ret = ((curr_equity - prev_equity) / prev_equity) * 100
                returns.append(ret)
        
        if len(returns) < 2:
            return 0.0
        
        return statistics.stdev(returns)
    
    def _identify_active_drawdown_cluster(self, current_time: datetime) -> Optional[DrawdownCluster]:
        """Check if currently in an active drawdown cluster."""
        if len(self.equity_history) < 2:
            return None
        
        current_equity = self.equity_history[-1][1]
        peak = self.equity_history[-1][1]
        
        # Find highest equity in last 30 minutes (approximate cluster window)
        for timestamp, equity in reversed(self.equity_history):
            if (current_time - timestamp).total_seconds() > 1800:  # 30 min
                break
            peak = max(peak, equity)
        
        if current_equity < peak:
            # In drawdown
            dd_pct = ((peak - current_equity) / peak) * 100 if peak > 0 else 0
            return DrawdownCluster(
                start_time=current_time - timedelta(minutes=10),  # Approximate
                end_time=current_time,
                duration_minutes=10,  # Approximate
                max_drawdown_pct=dd_pct,
                recovery_time_minutes=None,
            )
        
        return None
    
    def finalize_cluster(self, cluster: DrawdownCluster) -> None:
        """Mark drawdown cluster as completed."""
        self.drawdown_clusters.append(cluster)
    
    def get_equity_trend(self, lookback_minutes: int = 60) -> List[tuple[datetime, float]]:
        """Recent equity history."""
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
        return [
            (ts, equity) for ts, equity in self.equity_history
            if ts >= cutoff_time
        ]
    
    def flag_volatility_spike(self, threshold_pct: float = 5.0) -> bool:
        """Check if intraday volatility exceeds threshold."""
        return self._calculate_equity_volatility() > threshold_pct
