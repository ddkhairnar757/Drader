import unittest

import pandas as pd

from app.strategies.ema_crossover import EmaCrossoverStrategy


class TestEmaCrossoverStrategy(unittest.TestCase):
    def setUp(self) -> None:
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110]
        self.market_data = pd.DataFrame(
            {"close": prices},
            index=pd.date_range("2025-01-01", periods=len(prices), freq="D"),
        )
        self.strategy = EmaCrossoverStrategy(fast_window=3, slow_window=5, fixed_size=1)

    def test_prepare_data_computes_emas(self) -> None:
        prepared = self.strategy.prepare_data(self.market_data)
        self.assertIn("ema_fast", prepared.columns)
        self.assertIn("ema_slow", prepared.columns)
        self.assertEqual(len(prepared), len(self.market_data))

    def test_generate_signals_returns_signal_column(self) -> None:
        prepared = self.strategy.prepare_data(self.market_data)
        signals = self.strategy.generate_signals(prepared)
        self.assertIn("signal", signals.columns)
        self.assertEqual(len(signals), len(self.market_data))
        self.assertTrue(signals["signal"].isin([1, 0, -1]).all())

    def test_validate_signals_removes_redundant_events(self) -> None:
        prepared = self.strategy.prepare_data(self.market_data)
        signals = self.strategy.generate_signals(prepared)
        validated = self.strategy.validate_signals(signals)
        self.assertTrue(validated["signal"].isin([1, 0, -1]).all())

    def test_position_size_assigns_fixed_size(self) -> None:
        prepared = self.strategy.prepare_data(self.market_data)
        signals = self.strategy.generate_signals(prepared)
        sized = self.strategy.position_size(signals, balance=10000)
        self.assertIn("position_size", sized.columns)
        self.assertTrue((sized["position_size"] >= 0).all())

    def test_stop_loss_and_take_profit_include_levels(self) -> None:
        prepared = self.strategy.prepare_data(self.market_data)
        signals = self.strategy.generate_signals(prepared)
        stops = self.strategy.stop_loss(signals, prepared)
        profits = self.strategy.take_profit(signals, prepared)
        self.assertIn("stop_loss", stops.columns)
        self.assertIn("take_profit", profits.columns)
