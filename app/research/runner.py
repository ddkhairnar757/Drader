from __future__ import annotations

import argparse
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.backtesting.engine import BacktestEngine
from app.config.settings import BacktestSettings
from app.research.storage import ExperimentStorage
from app.visualization.equity_curve import plot_equity_curve
from app.market_data.nifty_loader import HistoricalMarketDataLoader
from app.strategies.ema_crossover import EmaCrossoverStrategy
from experiments.experiment import ExperimentRecord


class BacktestRunner:
    def __init__(self, settings: BacktestSettings | None = None, storage: ExperimentStorage | None = None) -> None:
        self.settings = settings or BacktestSettings.from_env()
        self.engine = BacktestEngine(settings=self.settings)
        self.storage = storage or ExperimentStorage()

    def _generate_experiment_id(self, strategy_name: str) -> str:
        return f"EXP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{strategy_name.replace(' ', '_')}-{uuid.uuid4().hex[:8]}"

    def run(
        self,
        strategy_name: str,
        market_data: pd.DataFrame,
        dataset: str,
        timeframe: str,
        notes: str | None = None,
        parameters: dict[str, float] | None = None,
    ) -> ExperimentRecord:
        if strategy_name == "ema_crossover":
            strategy = EmaCrossoverStrategy(
                fast_window=int(parameters.get("fast_window", 9)) if parameters else 9,
                slow_window=int(parameters.get("slow_window", 21)) if parameters else 21,
                fixed_size=int(parameters.get("fixed_size", 1)) if parameters else 1,
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        experiment_id = self._generate_experiment_id(strategy.name)
        record = ExperimentRecord(
            experiment_id=experiment_id,
            name=f"{strategy.name} backtest",
            strategy=strategy.name,
            dataset=dataset,
            timeframe=timeframe,
            brokerage=self.settings.commission_per_trade,
            slippage=self.settings.slippage_pct,
            start_time=datetime.now(timezone.utc),
            settings={
                "starting_capital": self.settings.starting_capital,
                "commission_per_trade": self.settings.commission_per_trade,
                "slippage_pct": self.settings.slippage_pct,
                "risk_per_trade": self.settings.risk_per_trade,
                "max_position_size": self.settings.max_position_size,
            },
            parameters=parameters or {},
            notes=notes,
        )

        result = self.engine.run(strategy, market_data)
        record.complete(result.metrics)
        save_path = self.storage.save(record, result.equity_curve)
        return record

    @staticmethod
    def load_market_data(source: str) -> pd.DataFrame:
        return HistoricalMarketDataLoader(source).load()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a standardized backtest and save the experiment.")
    parser.add_argument("--strategy", required=True, help="Strategy key, e.g. ema_crossover")
    parser.add_argument("--source", required=True, help="CSV file path for historical market data")
    parser.add_argument("--dataset", default="unknown", help="Dataset metadata label")
    parser.add_argument("--timeframe", default="daily", help="Data timeframe label")
    parser.add_argument("--notes", default="", help="Optional notes for the experiment")
    parser.add_argument("--fast-window", type=int, default=9, help="Fast EMA window")
    parser.add_argument("--slow-window", type=int, default=21, help="Slow EMA window")
    parser.add_argument("--fixed-size", type=int, default=1, help="Fixed position size")

    args = parser.parse_args()
    market_data = BacktestRunner.load_market_data(args.source)
    runner = BacktestRunner()
    record = runner.run(
        strategy_name=args.strategy,
        market_data=market_data,
        dataset=args.dataset,
        timeframe=args.timeframe,
        notes=args.notes,
        parameters={
            "fast_window": float(args.fast_window),
            "slow_window": float(args.slow_window),
            "fixed_size": float(args.fixed_size),
        },
    )

    print(f"Experiment saved: {record.experiment_id}")
    print(f"Metrics: {record.metrics}")


if __name__ == "__main__":
    main()
