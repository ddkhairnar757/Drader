import unittest

import pandas as pd

from app.backtesting.trade import Trade
from app.strategies.ema_crossover import EmaCrossoverStrategy
from app.validation.monte_carlo import MonteCarloSimulator
from app.validation.overfitting_check import OverfittingChecker
from app.validation.regime_analysis import RegimeAnalyzer
from app.validation.stress_test import StressScenario, StressTester
from app.validation.walk_forward import WalkForwardValidator


class TestValidationModules(unittest.TestCase):
    def setUp(self) -> None:
        prices = [100 + i * 0.5 for i in range(50)]
        self.market_data = pd.DataFrame(
            {"close": prices},
            index=pd.date_range("2025-01-01", periods=len(prices), freq="D"),
        )
        self.strategy_factory = lambda: EmaCrossoverStrategy(fast_window=2, slow_window=5, fixed_size=1)

    def test_walk_forward_validator(self) -> None:
        validator = WalkForwardValidator()
        results = validator.validate(
            self.strategy_factory,
            self.market_data,
            training_length=10,
            testing_length=5,
            step=5,
        )

        self.assertTrue(len(results) > 0)
        for result in results:
            self.assertIn("trade_count", result.train_metrics)
            self.assertIn("trade_count", result.test_metrics)
            self.assertLessEqual(result.train_period_start, result.train_period_end)
            self.assertLessEqual(result.test_period_start, result.test_period_end)

    def test_regime_analyzer(self) -> None:
        analyzer = RegimeAnalyzer()
        labels = analyzer.label_regimes(self.market_data, window=3, volatility_threshold=0.01, trend_threshold=0.001)
        self.assertEqual(len(labels), len(self.market_data))
        self.assertIn(labels.iloc[-1], {"bull", "bear", "volatile", "sideways", "unknown"})

        results = analyzer.run_regime_analysis(self.strategy_factory, self.market_data, labels)
        self.assertTrue(isinstance(results, list))
        if results:
            self.assertTrue(all(hasattr(r, "metrics") for r in results))

    def test_stress_tester_scenarios(self) -> None:
        tester = StressTester()
        scenarios = [
            StressScenario(name="baseline", commission_multiplier=1.0, slippage_multiplier=1.0),
            StressScenario(name="high_cost", commission_multiplier=2.0, slippage_multiplier=2.0),
        ]
        results = tester.run_scenarios(self.strategy_factory, self.market_data, scenarios)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].scenario.name, "baseline")
        self.assertEqual(results[1].scenario.name, "high_cost")
        self.assertIn("total_return", results[0].metrics)

    def test_monte_carlo_simulator(self) -> None:
        trades = [
            Trade(entry_dt=pd.Timestamp("2025-01-01"), entry_price=100.0, quantity=1, realized_pnl=5.0),
            Trade(entry_dt=pd.Timestamp("2025-01-02"), entry_price=101.0, quantity=1, realized_pnl=-2.0),
            Trade(entry_dt=pd.Timestamp("2025-01-03"), entry_price=102.0, quantity=1, realized_pnl=3.0),
        ]
        simulator = MonteCarloSimulator(seed=42)
        results = simulator.simulate(trades, starting_capital=100_000.0, n_simulations=10)

        self.assertEqual(len(results), 10)
        self.assertTrue(all(isinstance(result.total_return, float) for result in results))
        self.assertTrue(all(isinstance(result.max_drawdown, float) for result in results))

    def test_overfitting_checker(self) -> None:
        checker = OverfittingChecker(sharpe_threshold=0.5, win_rate_threshold=0.6)
        metrics = {
            "sharpe_ratio": 1.2,
            "win_rate": 0.75,
            "profit_factor": 3.5,
            "trade_count": 15,
            "annualized_return": 0.25,
        }
        result = checker.evaluate_metrics(metrics)
        self.assertEqual(result.warning, "high_overfitting_risk")

        train_metrics = {"sharpe_ratio": 1.5, "annualized_return": 0.30}
        test_metrics = {"sharpe_ratio": 0.2, "annualized_return": 0.10}
        compare_result = checker.compare_train_test(train_metrics, test_metrics)
        self.assertIn("delta_sharpe", compare_result.details)
        self.assertIn(compare_result.warning, {"low_out_of_sample_instability", "moderate_out_of_sample_instability", "high_out_of_sample_instability"})


if __name__ == "__main__":
    unittest.main()
