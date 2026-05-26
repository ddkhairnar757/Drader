"""
Position Panel
==============

Real-time position tracking, unrealized P&L monitoring, exposure management.

Purpose: Enable observation of portfolio composition, concentration risk, 
leverage usage, and position behavior patterns.

Design:
- Tracks current open positions with real-time P&L
- Calculates total exposure and exposure ratio
- Flags leverage, concentration, or sizing issues
- Monitors position duration and holding patterns
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum


class PositionStatus(Enum):
    """Position state."""
    SMALL = "small"           # < 2% exposure
    NORMAL = "normal"         # 2–10% exposure
    CONCENTRATED = "concentrated"  # 10–20% exposure
    OVER_CONCENTRATED = "over_concentrated"  # > 20% exposure
    BUILDING = "building"     # Average price dropping (buying more)
    LIQUIDATING = "liquidating"  # Reducing exposure


class ExposureWarning(Enum):
    """Risk flags."""
    NONE = "none"
    MILD_LEVERAGE = "mild_leverage"        # 60–80% of capital deployed
    HEAVY_LEVERAGE = "heavy_leverage"      # 80%+ of capital deployed
    SINGLE_STOCK_CONCENTRATION = "single_stock_concentration"  # > 20% in one stock
    SECTOR_CONCENTRATION = "sector_concentration"  # Too much in one sector
    POSITION_TOO_LONG = "position_too_long"  # Holding > 4 hours
    TOO_MANY_POSITIONS = "too_many_positions"  # > 10 open positions


@dataclass
class PositionSnapshot:
    """Point-in-time position state."""
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    exposure_pct: float  # % of total capital
    
    entry_time: datetime
    holding_duration_minutes: float
    
    # Position tracking
    average_entry_price: Optional[float] = None
    trades_in_position: int = 1
    status: PositionStatus = PositionStatus.NORMAL
    
    # Behavioral flags
    is_profitable: bool = field(init=False)
    is_building: bool = False  # Adding more
    is_liquidating: bool = False  # Reducing
    
    def __post_init__(self):
        self.is_profitable = self.unrealized_pnl > 0


@dataclass
class PortfolioExposure:
    """Portfolio-level exposure metrics."""
    total_capital: float
    deployed_capital: float
    available_cash: float
    deployment_ratio: float  # deployed / total
    
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    
    open_positions_count: int
    largest_position_exposure_pct: float
    
    # Risk flags
    warnings: List[ExposureWarning] = field(default_factory=list)
    exposure_rating: str = "normal"  # normal, caution, warning, critical


class PositionPanel:
    """Real-time position monitoring and exposure management."""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, PositionSnapshot] = {}
        self.position_history: List[PositionSnapshot] = []
        
    def record_position_update(
        self,
        symbol: str,
        quantity: int,
        entry_price: float,
        current_price: float,
        entry_time: datetime,
    ) -> None:
        """Update position snapshot."""
        if quantity == 0:
            # Position closed
            if symbol in self.positions:
                del self.positions[symbol]
            return
        
        unrealized_pnl = (current_price - entry_price) * quantity
        unrealized_pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        exposure_pct = (abs(current_price * quantity) / self.initial_capital) * 100
        
        holding_duration = (datetime.now() - entry_time).total_seconds() / 60
        
        status = self._determine_position_status(exposure_pct)
        
        snapshot = PositionSnapshot(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            exposure_pct=exposure_pct,
            entry_time=entry_time,
            holding_duration_minutes=holding_duration,
            status=status,
        )
        
        self.positions[symbol] = snapshot
    
    def get_portfolio_exposure(self) -> PortfolioExposure:
        """Portfolio-level metrics."""
        deployed_capital = sum(
            abs(pos.current_price * pos.quantity) for pos in self.positions.values()
        )
        deployed_pct = (deployed_capital / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        total_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_pnl_pct = (total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        largest_exposure = max(
            (pos.exposure_pct for pos in self.positions.values()),
            default=0.0
        )
        
        warnings = self._assess_warnings(deployed_pct, largest_exposure, len(self.positions))
        
        rating = self._exposure_rating(warnings)
        
        return PortfolioExposure(
            total_capital=self.initial_capital,
            deployed_capital=deployed_capital,
            available_cash=self.initial_capital - deployed_capital,
            deployment_ratio=deployed_pct / 100,
            total_unrealized_pnl=total_pnl,
            total_unrealized_pnl_pct=total_pnl_pct,
            open_positions_count=len(self.positions),
            largest_position_exposure_pct=largest_exposure,
            warnings=warnings,
            exposure_rating=rating,
        )
    
    def get_position_snapshot(self, symbol: str) -> Optional[PositionSnapshot]:
        """Single position details."""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[PositionSnapshot]:
        """All open positions."""
        return list(self.positions.values())
    
    def _determine_position_status(self, exposure_pct: float) -> PositionStatus:
        """Classify position size."""
        if exposure_pct < 2:
            return PositionStatus.SMALL
        elif exposure_pct < 10:
            return PositionStatus.NORMAL
        elif exposure_pct < 20:
            return PositionStatus.CONCENTRATED
        else:
            return PositionStatus.OVER_CONCENTRATED
    
    def _assess_warnings(
        self,
        deployment_pct: float,
        largest_exposure_pct: float,
        position_count: int,
    ) -> List[ExposureWarning]:
        """Identify risk flags."""
        warnings = []
        
        if 60 <= deployment_pct < 80:
            warnings.append(ExposureWarning.MILD_LEVERAGE)
        elif deployment_pct >= 80:
            warnings.append(ExposureWarning.HEAVY_LEVERAGE)
        
        if largest_exposure_pct > 20:
            warnings.append(ExposureWarning.SINGLE_STOCK_CONCENTRATION)
        
        if position_count > 10:
            warnings.append(ExposureWarning.TOO_MANY_POSITIONS)
        
        return warnings
    
    def _exposure_rating(self, warnings: List[ExposureWarning]) -> str:
        """Overall exposure health."""
        if not warnings:
            return "normal"
        
        if any(w in warnings for w in [ExposureWarning.HEAVY_LEVERAGE, ExposureWarning.SINGLE_STOCK_CONCENTRATION]):
            return "critical"
        elif len(warnings) >= 2:
            return "warning"
        else:
            return "caution"
    
    def flag_overtrading(self, threshold_duration_minutes: int = 60) -> List[str]:
        """Positions held too short (possible overtrading)."""
        return [
            pos.symbol for pos in self.positions.values()
            if pos.holding_duration_minutes < threshold_duration_minutes
            and pos.unrealized_pnl_pct < 0.5  # Marginal profit
        ]
    
    def flag_long_holdings(self, threshold_minutes: int = 240) -> List[str]:
        """Positions held too long (intraday rule violation)."""
        return [
            pos.symbol for pos in self.positions.values()
            if pos.holding_duration_minutes > threshold_minutes
        ]
    
    def flag_losing_positions(self, threshold_pct: float = -2.0) -> List[str]:
        """Positions in deep drawdown."""
        return [
            pos.symbol for pos in self.positions.values()
            if pos.unrealized_pnl_pct < threshold_pct
        ]
