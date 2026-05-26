from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    """Standard contract for research strategies.

    This class defines the interface every strategy should implement.
    It does not execute trades. It only specifies how signals and risk
    metadata should be generated for research and backtesting.
    """

    name: str = "BaseStrategy"

    @abstractmethod
    def prepare_data(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """Clean and enrich raw market data with indicators."""
        raise NotImplementedError

    @abstractmethod
    def generate_signals(self, prepared_data: pd.DataFrame) -> pd.DataFrame:
        """Generate entry/exit signal labels from prepared data."""
        raise NotImplementedError

    @abstractmethod
    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Apply safety checks and normalization to raw signals."""
        raise NotImplementedError

    @abstractmethod
    def position_size(
        self,
        signals: pd.DataFrame,
        balance: float,
        risk_per_trade: float | None = None,
    ) -> pd.DataFrame:
        """Attach position sizing information to signals."""
        raise NotImplementedError

    @abstractmethod
    def stop_loss(
        self,
        signals: pd.DataFrame,
        prepared_data: pd.DataFrame,
    ) -> pd.DataFrame:
        """Annotate stop-loss levels for each signal."""
        raise NotImplementedError

    @abstractmethod
    def take_profit(
        self,
        signals: pd.DataFrame,
        prepared_data: pd.DataFrame,
    ) -> pd.DataFrame:
        """Annotate take-profit levels for each signal."""
        raise NotImplementedError
