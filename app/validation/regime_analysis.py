from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from app.backtesting.engine import BacktestEngine, BacktestResult
from app.config.settings import BacktestSettings
from app.strategies.base_strategy import BaseStrategy


@dataclass
class RegimeResult:
    regime_label: str
    period_start: pd.Timestamp
    period_end: pd.Timestamp
    metrics: dict[str, float]
    backtest_result: BacktestResult


class RegimeAnalyzer:
    def __init__(self, settings: BacktestSettings | None = None) -> None:
        self.engine = BacktestEngine(settings=settings)

    def label_regimes(
        self,
        market_data: pd.DataFrame,
        window: int = 20,
        volatility_threshold: float = 0.02,
        trend_threshold: float = 0.005,
    ) -> pd.Series:
        returns = market_data["close"].pct_change()
        rolling_return = returns.rolling(window=window).mean()
        rolling_volatility = returns.rolling(window=window).std()

        labels = []
        for trend, vol in zip(rolling_return, rolling_volatility):
            if pd.isna(trend) or pd.isna(vol):
                labels.append("unknown")
            elif trend > trend_threshold and vol < volatility_threshold:
                labels.append("bull")
            elif trend < -trend_threshold and vol < volatility_threshold:
                labels.append("bear")
            elif vol >= volatility_threshold:
                labels.append("volatile")
            else:
                labels.append("sideways")

        return pd.Series(labels, index=market_data.index, name="regime")

    def run_regime_analysis(
        self,
        strategy_factory: Callable[[], BaseStrategy],
        market_data: pd.DataFrame,
        regime_labels: pd.Series,
    ) -> list[RegimeResult]:
        results: list[RegimeResult] = []
        grouped = regime_labels[regime_labels != "unknown"].groupby((regime_labels != regime_labels.shift()).cumsum())

        for _, segment in grouped:
            regime_label = segment.iloc[0]
            segment_data = market_data.loc[segment.index]
            if len(segment_data) < 10:
                continue
            strategy = strategy_factory()
            result = self.engine.run(strategy, segment_data)
            results.append(
                RegimeResult(
                    regime_label=regime_label,
                    period_start=segment_data.index[0],
                    period_end=segment_data.index[-1],
                    metrics=result.metrics,
                    backtest_result=result,
                )
            )
        return results
