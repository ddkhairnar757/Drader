from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class OverfittingCheckResult:
    warning: str
    score: float
    details: dict[str, Any]


class OverfittingChecker:
    def __init__(self, sharpe_threshold: float = 3.0, win_rate_threshold: float = 0.8) -> None:
        self.sharpe_threshold = sharpe_threshold
        self.win_rate_threshold = win_rate_threshold

    def evaluate_metrics(self, metrics: dict[str, float]) -> OverfittingCheckResult:
        score = 0.0
        details: dict[str, Any] = {}
        sharpe_ratio = metrics.get("sharpe_ratio", 0.0)
        win_rate = metrics.get("win_rate", 0.0)
        profit_factor = metrics.get("profit_factor", 0.0)
        trade_count = metrics.get("trade_count", 0)

        if sharpe_ratio > self.sharpe_threshold:
            score += 1.0
            details["high_sharpe"] = sharpe_ratio
        if win_rate > self.win_rate_threshold:
            score += 1.0
            details["high_win_rate"] = win_rate
        if profit_factor > 3.0:
            score += 0.5
            details["high_profit_factor"] = profit_factor
        if trade_count < 20:
            score += 0.5
            details["low_trade_count"] = trade_count

        if score >= 2.0:
            warning = "high_overfitting_risk"
        elif score >= 1.0:
            warning = "moderate_overfitting_risk"
        else:
            warning = "low_overfitting_risk"

        details.update(
            {
                "sharpe_ratio": sharpe_ratio,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "trade_count": trade_count,
            }
        )
        return OverfittingCheckResult(warning=warning, score=score, details=details)

    def compare_train_test(
        self,
        train_metrics: dict[str, float],
        test_metrics: dict[str, float],
    ) -> OverfittingCheckResult:
        annual_return_ratio = 0.0
        if train_metrics.get("annualized_return") and test_metrics.get("annualized_return"):
            annual_return_ratio = float(test_metrics["annualized_return"] / max(train_metrics["annualized_return"], 1e-9))

        delta_sharpe = abs(train_metrics.get("sharpe_ratio", 0.0) - test_metrics.get("sharpe_ratio", 0.0))
        details = {
            "annual_return_ratio": annual_return_ratio,
            "delta_sharpe": delta_sharpe,
            "train_sharpe": train_metrics.get("sharpe_ratio", 0.0),
            "test_sharpe": test_metrics.get("sharpe_ratio", 0.0),
        }
        score = 0.0
        if annual_return_ratio < 0.6:
            score += 1.0
            details["weak_out_of_sample_return"] = annual_return_ratio
        if delta_sharpe > 1.5:
            score += 1.0
            details["high_sharpe_shift"] = delta_sharpe

        if score >= 2.0:
            warning = "high_out_of_sample_instability"
        elif score >= 1.0:
            warning = "moderate_out_of_sample_instability"
        else:
            warning = "low_out_of_sample_instability"

        return OverfittingCheckResult(warning=warning, score=score, details=details)
