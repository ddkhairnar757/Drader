import unittest

import pandas as pd

from app.reports.equity_review import EquityReview
from app.reports.risk_report import RiskReport
from app.reports.research_report import ResearchReportBuilder
from app.reports.validation_summary import ValidationSummary
from app.validation.overfitting_check import OverfittingCheckResult
from app.validation.regime_analysis import RegimeResult
from app.validation.stress_test import StressResult, StressScenario
from app.validation.walk_forward import WalkForwardResult
from experiments.experiment import ExperimentRecord


class TestReportGeneration(unittest.TestCase):
    def setUp(self) -> None:
        self.experiment = ExperimentRecord(
            experiment_id="EXP-20260526-TEST-0001",
            name="Test strategy backtest",
            strategy="EMA Crossover",
            dataset="synthetic",
            timeframe="daily",
            brokerage=1.0,
            slippage=0.0005,
            start_time=pd.Timestamp("2025-01-01"),
            settings={"starting_capital": 100000.0},
            parameters={"fast_window": 2, "slow_window": 5},
            notes="report test",
        )
        self.equity_curve = pd.DataFrame(
            {"equity": [100000.0, 100500.0, 100200.0, 100800.0, 100900.0]},
            index=pd.date_range("2025-01-01", periods=5, freq="D"),
        )
        self.metrics = {
            "total_return": 0.009,
            "annualized_return": 0.18,
            "max_drawdown": -0.006,
            "sharpe_ratio": 1.2,
            "profit_factor": 1.8,
            "trade_count": 4.0,
        }
        self.walk_forward_results = [
            WalkForwardResult(
                train_period_start=pd.Timestamp("2025-01-01"),
                train_period_end=pd.Timestamp("2025-01-02"),
                test_period_start=pd.Timestamp("2025-01-03"),
                test_period_end=pd.Timestamp("2025-01-04"),
                train_metrics=self.metrics,
                test_metrics=self.metrics,
                train_result=None,
                test_result=None,
            )
        ]
        self.regime_results = [
            RegimeResult(
                regime_label="bull",
                period_start=pd.Timestamp("2025-01-01"),
                period_end=pd.Timestamp("2025-01-03"),
                metrics=self.metrics,
                backtest_result=None,
            )
        ]
        self.stress_results = [
            StressResult(
                scenario=StressScenario(name="baseline", commission_multiplier=1.0, slippage_multiplier=1.0),
                metrics=self.metrics,
                backtest_result=None,
            )
        ]
        self.overfitting_result = OverfittingCheckResult(
            warning="low_overfitting_risk",
            score=0.0,
            details={},
        )

    def test_validation_summary_scores(self) -> None:
        summary = ValidationSummary.summarize(
            self.walk_forward_results,
            self.regime_results,
            self.stress_results,
            self.overfitting_result,
        )
        self.assertIn("overall_score", summary)
        self.assertGreaterEqual(summary["overall_score"], 0.0)
        self.assertLessEqual(summary["overall_score"], 10.0)

    def test_equity_review_analysis(self) -> None:
        review = EquityReview.analyze(self.equity_curve)
        self.assertGreaterEqual(review.smoothness_score, 0.0)
        self.assertLessEqual(review.smoothness_score, 10.0)
        self.assertEqual(review.total_periods, 5)

    def test_risk_report_analysis(self) -> None:
        report = RiskReport.analyze(self.equity_curve)
        self.assertIn("tail_risk_5", report.__dict__)
        self.assertIsInstance(report.max_consecutive_loss_days, int)

    def test_research_report_builder(self) -> None:
        equity_review = EquityReview.analyze(self.equity_curve)
        risk_report = RiskReport.analyze(self.equity_curve)
        validation_summary = ValidationSummary.summarize(
            self.walk_forward_results,
            self.regime_results,
            self.stress_results,
            self.overfitting_result,
        )
        builder = ResearchReportBuilder()
        report = builder.build(
            self.experiment,
            metrics_summary=self.metrics,
            validation_summary=validation_summary,
            equity_review=equity_review,
            risk_report=risk_report,
        )

        self.assertGreaterEqual(report.confidence_score, 0.0)
        self.assertLessEqual(report.confidence_score, 10.0)
        self.assertIsInstance(report.conclusions, list)
        self.assertIn("strategy", report.experiment_metadata)


if __name__ == "__main__":
    unittest.main()
