from __future__ import annotations

import pandas as pd

from .base_strategy import BaseStrategy


class EmaCrossoverStrategy(BaseStrategy):
    """Simple EMA crossover strategy used as a contract example.

    This strategy is intentionally simple. It exists to demonstrate a clean
    research strategy implementation that follows the BaseStrategy contract.
    """

    name = "EMA Crossover"

    def __init__(self, fast_window: int = 9, slow_window: int = 21, fixed_size: int = 1) -> None:
        if fast_window >= slow_window:
            raise ValueError("fast_window must be smaller than slow_window")

        self.fast_window = fast_window
        self.slow_window = slow_window
        self.fixed_size = fixed_size

    def prepare_data(self, market_data: pd.DataFrame) -> pd.DataFrame:
        if "close" not in market_data.columns:
            raise ValueError("Market data must contain a 'close' column.")

        data = market_data.copy()
        data["ema_fast"] = data["close"].ewm(span=self.fast_window, adjust=False).mean()
        data["ema_slow"] = data["close"].ewm(span=self.slow_window, adjust=False).mean()
        return data

    def generate_signals(self, prepared_data: pd.DataFrame) -> pd.DataFrame:
        signals = pd.DataFrame(index=prepared_data.index)
        signals["signal"] = 0

        crossover_up = prepared_data["ema_fast"] > prepared_data["ema_slow"]
        crossover_down = prepared_data["ema_fast"] < prepared_data["ema_slow"]

        previous_up = crossover_up.shift(1).fillna(False)
        previous_down = crossover_down.shift(1).fillna(False)

        signals.loc[crossover_up & (previous_up == False), "signal"] = 1
        signals.loc[crossover_down & (previous_down == False), "signal"] = -1
        return signals

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        validated = signals.copy()
        validated["signal"] = validated["signal"].fillna(0).astype(int)
        validated.loc[validated["signal"].diff().fillna(0) == 0, "signal"] = 0
        return validated

    def position_size(
        self,
        signals: pd.DataFrame,
        balance: float,
        risk_per_trade: float | None = None,
    ) -> pd.DataFrame:
        positions = signals.copy()
        positions["position_size"] = self.fixed_size
        positions.loc[positions["signal"] == 0, "position_size"] = 0
        return positions

    def stop_loss(self, signals: pd.DataFrame, prepared_data: pd.DataFrame) -> pd.DataFrame:
        stops = signals.copy()
        entry_mask = stops["signal"] != 0
        stops["stop_loss"] = prepared_data.loc[:, "close"].where(entry_mask, None) * 0.98
        return stops

    def take_profit(self, signals: pd.DataFrame, prepared_data: pd.DataFrame) -> pd.DataFrame:
        profits = signals.copy()
        entry_mask = profits["signal"] != 0
        profits["take_profit"] = prepared_data.loc[:, "close"].where(entry_mask, None) * 1.02
        return profits
