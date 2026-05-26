from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from app.backtesting.engine import BacktestEngine, BacktestResult
from app.config.settings import BacktestSettings
from app.strategies.base_strategy import BaseStrategy


@dataclass
class WalkForwardResult:
    train_period_start: pd.Timestamp
    train_period_end: pd.Timestamp
    test_period_start: pd.Timestamp
    test_period_end: pd.Timestamp
    train_metrics: dict[str, float]
    test_metrics: dict[str, float]
    train_result: BacktestResult
    test_result: BacktestResult


class WalkForwardValidator:
    def __init__(self, settings: BacktestSettings | None = None) -> None:
        self.engine = BacktestEngine(settings=settings)

    def split_windows(
        self,
        market_data: pd.DataFrame,
        training_length: int,
        testing_length: int,
        step: int,
    ) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
        windows: list[tuple[pd.DataFrame, pd.DataFrame]] = []
        total = len(market_data)
        start = 0
        while start + training_length + testing_length <= total:
            train = market_data.iloc[start : start + training_length]
            test = market_data.iloc[start + training_length : start + training_length + testing_length]
            windows.append((train, test))
            start += step
        return windows

    def validate(
        self,
        strategy_factory: Callable[[], BaseStrategy],
        market_data: pd.DataFrame,
        training_length: int,
        testing_length: int,
        step: int,
    ) -> list[WalkForwardResult]:
        results: list[WalkForwardResult] = []
        windows = self.split_windows(market_data, training_length, testing_length, step)
        for train_data, test_data in windows:
            train_strategy = strategy_factory()
            test_strategy = strategy_factory()
            train_result = self.engine.run(train_strategy, train_data)
            test_result = self.engine.run(test_strategy, test_data)
            results.append(
                WalkForwardResult(
                    train_period_start=train_data.index[0],
                    train_period_end=train_data.index[-1],
                    test_period_start=test_data.index[0],
                    test_period_end=test_data.index[-1],
                    train_metrics=train_result.metrics,
                    test_metrics=test_result.metrics,
                    train_result=train_result,
                    test_result=test_result,
                )
            )
        return results
