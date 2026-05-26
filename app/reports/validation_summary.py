from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from app.validation.overfitting_check import OverfittingCheckResult
from app.validation.regime_analysis import RegimeResult
from app.validation.stress_test import StressResult
from app.validation.walk_forward import WalkForwardResult


@dataclass
class ValidationScores:
    walk_forward_score: float
    regime_score: float
    stress_score: float
    overfitting_score: float
    overall_score: float


class ValidationSummary:
    @staticmethod
    def score_walk_forward(results: Iterable[WalkForwardResult]) -> float:
        test_returns = np.array([
            result.test_metrics.get("total_return", 0.0)
            for result in results
            if result.test_metrics and "total_return" in result.test_metrics
        ], dtype=float)
        if test_returns.size == 0:
            return 0.0

        positive_ratio = float(np.mean(test_returns > 0))
        mean_return = float(np.mean(test_returns))
        volatility = float(np.std(test_returns, ddof=0))
        stability = 1.0 - min(1.0, volatility / (abs(mean_return) + 0.05))
        score = 10.0 * (0.6 * positive_ratio + 0.4 * stability)
        return float(np.clip(score, 0.0, 10.0))

    @staticmethod
    def score_regime_survivability(results: Iterable[RegimeResult]) -> float:
        regimes = list(results)
        if not regimes:
            return 0.0

        positive = sum(1 for result in regimes if result.metrics.get("total_return", 0.0) >= 0)
        score = 10.0 * positive / len(regimes)
        return float(np.clip(score, 0.0, 10.0))

    @staticmethod
    def score_stress_resistance(results: Iterable[StressResult]) -> float:
        scenarios = [result for result in results if result.metrics is not None]
        if not scenarios:
            return 0.0

        baseline = next((result for result in scenarios if result.scenario.name == "baseline"), scenarios[0])
        baseline_return = baseline.metrics.get("total_return", 0.0)
        worst_return = min(result.metrics.get("total_return", 0.0) for result in scenarios)

        if baseline_return == 0.0:
            return 0.0

        resistance = 1.0 - min(1.0, abs(baseline_return - worst_return) / (abs(baseline_return) + 1e-9))
        score = 10.0 * resistance
        return float(np.clip(score, 0.0, 10.0))

    @staticmethod
    def score_overfitting(result: OverfittingCheckResult) -> float:
        mapping = {
            "low_overfitting_risk": 10.0,
            "moderate_overfitting_risk": 6.0,
            "high_overfitting_risk": 2.0,
            "low_out_of_sample_instability": 10.0,
            "moderate_out_of_sample_instability": 6.0,
            "high_out_of_sample_instability": 2.0,
        }
        return mapping.get(result.warning, 5.0)

    @classmethod
    def summarize(
        cls,
        walk_forward_results: Iterable[WalkForwardResult],
        regime_results: Iterable[RegimeResult],
        stress_results: Iterable[StressResult],
        overfitting_result: OverfittingCheckResult,
    ) -> dict[str, object]:
        walk_forward_score = cls.score_walk_forward(walk_forward_results)
        regime_score = cls.score_regime_survivability(regime_results)
        stress_score = cls.score_stress_resistance(stress_results)
        overfitting_score = cls.score_overfitting(overfitting_result)
        overall_score = float(
            np.mean([walk_forward_score, regime_score, stress_score, overfitting_score])
        )

        return {
            "walk_forward_score": walk_forward_score,
            "regime_score": regime_score,
            "stress_score": stress_score,
            "overfitting_score": overfitting_score,
            "overall_score": overall_score,
            "scores": ValidationScores(
                walk_forward_score=walk_forward_score,
                regime_score=regime_score,
                stress_score=stress_score,
                overfitting_score=overfitting_score,
                overall_score=overall_score,
            ),
        }
