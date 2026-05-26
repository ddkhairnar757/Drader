"""
Signal Monitor
==============

Real-time signal tracking, execution flow monitoring, signal distribution analysis.

Purpose: Enable observation of strategy signal generation patterns, execution fidelity,
and detection of overtrading or false signal behavior.

Design:
- Captures all signal events with metadata
- Tracks execution lag (signal to fill time)
- Analyzes signal distribution (buy/sell ratio, frequency)
- Flags suspicious patterns (clustering, overtrading, contradictions)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum


class SignalSide(Enum):
    """Trade direction."""
    BUY = "buy"
    SELL = "sell"


class SignalStatus(Enum):
    """Signal lifecycle state."""
    GENERATED = "generated"        # Created, not yet routed
    ROUTED = "routed"             # Sent to execution
    PARTIALLY_EXECUTED = "partially_executed"  # Some quantity filled
    EXECUTED = "executed"         # Fully filled
    CANCELLED = "cancelled"       # Cancelled before execution
    REJECTED = "rejected"         # Rejected by broker/validator


@dataclass
class SignalEvent:
    """Signal generation event."""
    timestamp: datetime
    strategy_name: str
    symbol: str
    side: SignalSide
    quantity: int
    reason: str
    
    status: SignalStatus = SignalStatus.GENERATED
    execution_timestamps: List[datetime] = field(default_factory=list)
    filled_quantity: int = 0
    execution_price: Optional[float] = None
    
    # Tracking
    signal_to_execution_seconds: Optional[float] = None
    signal_to_fill_seconds: Optional[float] = None


@dataclass
class SignalDistribution:
    """Signal pattern metrics."""
    total_signals: int
    buy_signals: int
    sell_signals_count: int
    buy_sell_ratio: float
    
    avg_signal_frequency_per_minute: float  # Signals / elapsed minutes
    signal_clustering_score: float  # 0–1, how bunched together
    
    # Quality metrics
    execution_rate: float  # Executed signals / total signals
    avg_time_to_execution_seconds: float
    cancelled_signals: int
    rejected_signals: int
    
    # Behavioral flags
    is_overtrading: bool = False  # > 1 signal per minute
    has_signal_clustering: bool = False  # Signals bunched in time
    has_contradictory_signals: bool = False  # Buy then sell quickly
    avg_filled_ratio: float = 1.0  # Avg filled qty / requested qty


class SignalMonitor:
    """Real-time signal tracking and analysis."""
    
    def __init__(self):
        self.signals: List[SignalEvent] = []
        self.signal_index: Dict[str, List[SignalEvent]] = {}  # symbol -> signals
        self.start_time: datetime = datetime.now()
    
    def record_signal(
        self,
        strategy_name: str,
        symbol: str,
        side: SignalSide,
        quantity: int,
        reason: str,
    ) -> SignalEvent:
        """Create and record new signal."""
        signal = SignalEvent(
            timestamp=datetime.now(),
            strategy_name=strategy_name,
            symbol=symbol,
            side=side,
            quantity=quantity,
            reason=reason,
        )
        
        self.signals.append(signal)
        
        if symbol not in self.signal_index:
            self.signal_index[symbol] = []
        self.signal_index[symbol].append(signal)
        
        return signal
    
    def record_execution(
        self,
        signal: SignalEvent,
        filled_quantity: int,
        execution_price: float,
    ) -> None:
        """Mark signal as executed."""
        signal.execution_timestamps.append(datetime.now())
        signal.filled_quantity += filled_quantity
        signal.execution_price = execution_price
        
        if signal.filled_quantity >= signal.quantity:
            signal.status = SignalStatus.EXECUTED
            signal.signal_to_fill_seconds = (
                (signal.execution_timestamps[-1] - signal.timestamp).total_seconds()
            )
        elif signal.filled_quantity > 0:
            signal.status = SignalStatus.PARTIALLY_EXECUTED
    
    def get_signal_distribution(self) -> SignalDistribution:
        """Signal pattern analysis."""
        if not self.signals:
            return SignalDistribution(
                total_signals=0,
                buy_signals=0,
                sell_signals_count=0,
                buy_sell_ratio=0,
                avg_signal_frequency_per_minute=0,
                signal_clustering_score=0,
                execution_rate=0,
                avg_time_to_execution_seconds=0,
                cancelled_signals=0,
                rejected_signals=0,
            )
        
        elapsed_minutes = max(
            (datetime.now() - self.start_time).total_seconds() / 60,
            1.0
        )
        
        buy_signals = sum(1 for s in self.signals if s.side == SignalSide.BUY)
        sell_signals = len(self.signals) - buy_signals
        buy_sell_ratio = buy_signals / max(sell_signals, 1)
        
        signal_frequency = len(self.signals) / elapsed_minutes
        
        clustering = self._calculate_clustering_score()
        
        executed_signals = [s for s in self.signals if s.status == SignalStatus.EXECUTED]
        execution_rate = len(executed_signals) / max(len(self.signals), 1)
        
        execution_times = [
            s.signal_to_fill_seconds
            for s in executed_signals
            if s.signal_to_fill_seconds is not None
        ]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        cancelled = sum(1 for s in self.signals if s.status == SignalStatus.CANCELLED)
        rejected = sum(1 for s in self.signals if s.status == SignalStatus.REJECTED)
        
        overtrading = signal_frequency > 1.0
        has_clustering = clustering > 0.6
        has_contradictions = self._check_contradictory_signals()
        
        filled_ratios = [
            s.filled_quantity / max(s.quantity, 1)
            for s in executed_signals
            if s.quantity > 0
        ]
        avg_filled = sum(filled_ratios) / len(filled_ratios) if filled_ratios else 1.0
        
        return SignalDistribution(
            total_signals=len(self.signals),
            buy_signals=buy_signals,
            sell_signals_count=sell_signals,
            buy_sell_ratio=buy_sell_ratio,
            avg_signal_frequency_per_minute=signal_frequency,
            signal_clustering_score=clustering,
            execution_rate=execution_rate,
            avg_time_to_execution_seconds=avg_execution_time,
            cancelled_signals=cancelled,
            rejected_signals=rejected,
            is_overtrading=overtrading,
            has_signal_clustering=has_clustering,
            has_contradictory_signals=has_contradictions,
            avg_filled_ratio=avg_filled,
        )
    
    def get_symbol_signals(self, symbol: str) -> List[SignalEvent]:
        """All signals for a symbol."""
        return self.signal_index.get(symbol, [])
    
    def _calculate_clustering_score(self) -> float:
        """How clustered signals are in time (0–1)."""
        if len(self.signals) < 2:
            return 0.0
        
        intervals = []
        for i in range(1, len(self.signals)):
            interval = (
                self.signals[i].timestamp - self.signals[i-1].timestamp
            ).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return 0.0
        
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        
        # Clustering score: how much are signals bunched (short intervals)
        # High score = bunched, low score = spread out
        clustering = 1 - (min(avg_interval, 60) / 60)
        return max(0, min(1, clustering))
    
    def _check_contradictory_signals(self) -> bool:
        """Detect buy then sell quickly (same symbol)."""
        for symbol, signals in self.signal_index.items():
            if len(signals) < 2:
                continue
            
            for i in range(len(signals) - 1):
                curr = signals[i]
                next_sig = signals[i + 1]
                
                # Check if opposite signals within 5 minutes
                time_gap = (next_sig.timestamp - curr.timestamp).total_seconds() / 60
                if (time_gap < 5 and
                    curr.side != next_sig.side):
                    return True
        
        return False
    
    def flag_overtrading(self, threshold_per_minute: float = 1.0) -> bool:
        """Check if signal rate exceeds threshold."""
        distribution = self.get_signal_distribution()
        return distribution.avg_signal_frequency_per_minute > threshold_per_minute
    
    def flag_signal_quality_issues(self) -> List[str]:
        """Identify concerning signal patterns."""
        flags = []
        distribution = self.get_signal_distribution()
        
        if distribution.is_overtrading:
            flags.append("overtrading_detected")
        
        if distribution.has_signal_clustering:
            flags.append("signal_clustering")
        
        if distribution.has_contradictory_signals:
            flags.append("contradictory_signals")
        
        if distribution.execution_rate < 0.5:
            flags.append("low_execution_rate")
        
        if distribution.cancelled_signals > distribution.total_signals * 0.2:
            flags.append("high_cancellation_rate")
        
        return flags
