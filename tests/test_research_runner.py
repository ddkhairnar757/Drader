import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.research.runner import BacktestRunner
from app.research.storage import ExperimentStorage
from app.strategies.ema_crossover import EmaCrossoverStrategy


class TestResearchRunner(unittest.TestCase):
    def test_runner_saves_experiment(self) -> None:
        prices = [100, 101, 102, 103, 104, 105, 104, 103]
        market_data = pd.DataFrame(
            {"close": prices},
            index=pd.date_range("2025-01-01", periods=len(prices), freq="D"),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ExperimentStorage(base_path=Path(temp_dir) / "storage")
            runner = BacktestRunner(storage=storage)
            record = runner.run(
                strategy_name="ema_crossover",
                market_data=market_data,
                dataset="NIFTY_sample",
                timeframe="daily",
                notes="runner test",
                parameters={"fast_window": 2.0, "slow_window": 5.0, "fixed_size": 1.0},
            )

            self.assertTrue(record.experiment_id.startswith("EXP-"))
            self.assertIsNotNone(record.metrics)
            self.assertTrue((storage.base_path / record.experiment_id).exists() or any("experiment.json" in str(p) for p in storage.base_path.rglob("experiment.json")))

    def test_runner_handles_unknown_strategy(self) -> None:
        runner = BacktestRunner()
        prices = [100, 101, 102]
        market_data = pd.DataFrame(
            {"close": prices},
            index=pd.date_range("2025-01-01", periods=len(prices), freq="D"),
        )
        with self.assertRaises(ValueError):
            runner.run(
                strategy_name="unknown_strategy",
                market_data=market_data,
                dataset="NIFTY_sample",
                timeframe="daily",
                notes="unknown strategy test",
            )
