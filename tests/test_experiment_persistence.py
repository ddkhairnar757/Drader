import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

from experiments.experiment import ExperimentRecord
from experiments.persistence import ExperimentPersistence


class TestExperimentPersistence(unittest.TestCase):
    def test_save_and_load_experiment(self) -> None:
        record = ExperimentRecord(
            experiment_id="EXP-20250101-EMA-TEST",
            name="EMA Crossover Experiment",
            strategy="EMA Crossover",
            dataset="NIFTY_sample",
            timeframe="daily",
            brokerage=1.0,
            slippage=0.0005,
            start_time=datetime(2025, 1, 1, 0, 0, 0),
            settings={"starting_capital": 100000.0},
            parameters={"fast_window": 2, "slow_window": 5},
            notes="test persistence",
        )
        equity_curve = pd.DataFrame(
            {"equity": [100000.0, 100500.0, 100300.0]},
            index=pd.date_range("2025-01-01", periods=3, freq="D"),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            persistence = ExperimentPersistence(base_path=Path(temp_dir) / "storage")
            experiment_dir = persistence.save_experiment(record, equity_curve)
            self.assertTrue((experiment_dir / "experiment.json").exists())
            self.assertTrue((experiment_dir / "equity_curve.csv").exists())

            loaded = persistence.load_experiment(experiment_dir / "experiment.json")
            self.assertEqual(loaded.strategy, record.strategy)
            self.assertEqual(loaded.dataset, record.dataset)
            self.assertEqual(loaded.notes, record.notes)


from app.visualization.equity_curve import plot_equity_curve
from app.visualization.metrics_dashboard import MetricsDashboard
from app.visualization.trade_plot import plot_trade_signals
from app.backtesting.trade import Trade


class TestVisualization(unittest.TestCase):
    def setUp(self) -> None:
        self.market_data = pd.DataFrame(
            {"close": [100, 101, 102, 101, 100, 102]},
            index=pd.date_range("2025-01-01", periods=6, freq="D"),
        )
        self.equity_curve = pd.DataFrame(
            {"equity": [100000.0, 100500.0, 100400.0, 100600.0, 100300.0, 100900.0]},
            index=self.market_data.index,
        )
        self.trades = [
            Trade(
                entry_dt=self.market_data.index[1],
                entry_price=101.0,
                quantity=1,
                exit_dt=self.market_data.index[4],
                exit_price=100.0,
                stop_loss=99.0,
                take_profit=104.0,
            )
        ]

    def test_plot_equity_curve_returns_figure(self) -> None:
        fig = plot_equity_curve(self.equity_curve)
        self.assertIsNotNone(fig)

    def test_plot_trade_signals_returns_figure(self) -> None:
        fig = plot_trade_signals(self.market_data, self.trades)
        self.assertIsNotNone(fig)

    def test_metrics_dashboard_summary(self) -> None:
        metrics = {
            "total_return": 0.009,
            "max_drawdown": -0.01,
            "win_rate": 0.5,
        }
        summary = MetricsDashboard.create_summary(metrics)
        self.assertEqual(len(summary), len(metrics))
