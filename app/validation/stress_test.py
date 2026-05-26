from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.backtesting.engine import BacktestEngine, BacktestResult
from app.config.settings import BacktestSettings
from app.strategies.base_strategy import BaseStrategy


@dataclass
class StressScenario:
    name: str
    commission_multiplier: float = 1.0
    slippage_multiplier: float = 1.0


@dataclass
class StressResult:
    scenario: StressScenario
    metrics: dict[str, float]
    backtest_result: BacktestResult


class StressTester:
    def __init__(self, base_settings: BacktestSettings | None = None) -> None:
        self.base_settings = base_settings or BacktestSettings()

    def run_scenarios(
        self,
        strategy_factory: Callable[[], BaseStrategy],
        market_data,
        scenarios: list[StressScenario],
    ) -> list[StressResult]:
        results: list[StressResult] = []
        for scenario in scenarios:
            settings = BacktestSettings(
                starting_capital=self.base_settings.starting_capital,
                commission_per_trade=self.base_settings.commission_per_trade * scenario.commission_multiplier,
                slippage_pct=self.base_settings.slippage_pct * scenario.slippage_multiplier,
                risk_per_trade=self.base_settings.risk_per_trade,
                max_position_size=self.base_settings.max_position_size,
            )
            engine = BacktestEngine(settings=settings)
            strategy = strategy_factory()
            result = engine.run(strategy, market_data)
            results.append(StressResult(scenario, result.metrics, result))
        return results
