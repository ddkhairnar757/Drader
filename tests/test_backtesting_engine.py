import unittest

import pandas as pd

from app.backtesting.engine import BacktestEngine
from app.config.settings import BacktestSettings
from app.strategies.ema_crossover import EmaCrossoverStrategy


class TestBacktestEngine(unittest.TestCase):
    def test_backtest_engine_runs_and_returns_metrics(self) -> None:
        prices = [100, 101, 102, 103, 104, 105, 104, 103, 102, 101, 100, 99, 100, 101, 102, 103]
        market_data = pd.DataFrame(
            {"close": prices},
            index=pd.date_range("2025-01-01", periods=len(prices), freq="D"),
        )

        strategy = EmaCrossoverStrategy(fast_window=2, slow_window=5, fixed_size=1)
        settings = BacktestSettings(
            starting_capital=100000.0,
            commission_per_trade=0.0,
            slippage_pct=0.0,
            risk_per_trade=0.01,
            max_position_size=10,
        )

        engine = BacktestEngine(settings=settings)
        result = engine.run(strategy, market_data)

        self.assertEqual(len(result.equity_curve), len(prices))
        self.assertIn("equity", result.equity_curve.columns)
        self.assertGreaterEqual(result.metrics["trade_count"], 0)
        self.assertGreaterEqual(result.metrics["total_return"], -1.0)
        self.assertIsInstance(result.trades, list)


if __name__ == "__main__":
    unittest.main()
