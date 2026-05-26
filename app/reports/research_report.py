from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from experiments.experiment import ExperimentRecord
from app.reports.equity_review import EquityReviewSummary
from app.reports.risk_report import RiskReportSummary
from app.reports.validation_summary import ValidationScores


@dataclass
class ResearchReport:
    experiment_metadata: dict[str, Any]
    metrics_summary: dict[str, float]
    validation_summary: dict[str, Any]
    equity_review: dict[str, Any]
    risk_report: dict[str, Any]
    confidence_score: float
    conclusions: list[str]


class ResearchReportBuilder:
    @staticmethod
    def _profitability_score(metrics: dict[str, float]) -> float:
        total_return = float(metrics.get("total_return", 0.0))
        sharpe_ratio = float(metrics.get("sharpe_ratio", 0.0))
        score = 10.0 * min(1.0, max(0.0, total_return * 5.0 + sharpe_ratio * 0.2))
        return float(np.clip(score, 0.0, 10.0))

    @staticmethod
    def _drawdown_stability_score(risk_report: dict[str, Any], equity_review: dict[str, Any]) -> float:
        drawdown_score = float(risk_report.get("capital_stress_score", 0.0))
        recovery_score = float(equity_review.get("recovery_score", 0.0))
        return float(np.clip((drawdown_score + recovery_score) / 2.0, 0.0, 10.0))

    @staticmethod
    def _conclusions(
        metrics: dict[str, float],
        validation_summary: dict[str, Any],
        risk_report: dict[str, Any],
    ) -> list[str]:
        conclusions: list[str] = []
        if metrics.get("total_return", 0.0) >= 0.0:
            conclusions.append("The strategy generated a non-negative return in the reference backtest.")
        else:
            conclusions.append("The strategy produced a negative return in the reference backtest.")

        overfitting_warning = validation_summary.get("scores")
        if isinstance(overfitting_warning, ValidationScores):
            if overfitting_warning.overfitting_score <= 4.0:
                conclusions.append("The strategy is at elevated risk of overfitting.")
            elif overfitting_warning.overfitting_score <= 7.0:
                conclusions.append("The strategy exhibits moderate overfitting risk.")
            else:
                conclusions.append("The strategy shows low detected overfitting risk.")
        else:
            if validation_summary.get("overfitting_score", 0.0) <= 4.0:
                conclusions.append("The strategy is at elevated risk of overfitting.")
            elif validation_summary.get("overfitting_score", 0.0) <= 7.0:
                conclusions.append("The strategy exhibits moderate overfitting risk.")
            else:
                conclusions.append("The strategy shows low detected overfitting risk.")

        if float(risk_report.get("max_drawdown", 0.0)) <= -0.2:
            conclusions.append("The equity curve has meaningful drawdown risk and requires tighter risk management.")
        else:
            conclusions.append("Drawdown risk remains within a reasonable range for the current backtest.")

        if float(validation_summary.get("overall_score", 0.0)) >= 7.5:
            conclusions.append("Validation results point toward a robust strategy with strong survivability signals.")
        elif float(validation_summary.get("overall_score", 0.0)) >= 4.0:
            conclusions.append("Validation results are mixed and deserve further stress testing and regime exploration.")
        else:
            conclusions.append("Validation results are weak and indicate that the strategy likely needs further refinement.")

        return conclusions

    def build(
        self,
        experiment: ExperimentRecord,
        metrics_summary: dict[str, float],
        validation_summary: dict[str, Any],
        equity_review: EquityReviewSummary | dict[str, Any],
        risk_report: RiskReportSummary | dict[str, Any],
    ) -> ResearchReport:
        experiment_metadata = {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "strategy": experiment.strategy,
            "dataset": experiment.dataset,
            "timeframe": experiment.timeframe,
            "brokerage": experiment.brokerage,
            "slippage": experiment.slippage,
            "start_time": experiment.start_time.isoformat(),
            "end_time": experiment.end_time.isoformat() if experiment.end_time else None,
            "settings": experiment.settings,
            "parameters": experiment.parameters,
            "notes": experiment.notes,
        }

        if hasattr(equity_review, "__dict__"):
            equity_review_data = equity_review.__dict__
        else:
            equity_review_data = equity_review

        if hasattr(risk_report, "__dict__"):
            risk_report_data = risk_report.__dict__
        else:
            risk_report_data = risk_report

        if isinstance(validation_summary.get("scores"), ValidationScores):
            validation_summary_data = validation_summary.copy()
            validation_summary_data["scores"] = validation_summary["scores"]
        else:
            validation_summary_data = validation_summary

        profitability_score = self._profitability_score(metrics_summary)
        drawdown_stability_score = self._drawdown_stability_score(risk_report_data, equity_review_data)
        regime_score = float(validation_summary_data.get("regime_score", 0.0))
        stress_score = float(validation_summary_data.get("stress_score", 0.0))
        overfitting_score = float(validation_summary_data.get("overfitting_score", 0.0))
        robustness_score = float(validation_summary_data.get("overall_score", 0.0))

        confidence_score = float(
            sum(
                [
                    profitability_score,
                    robustness_score,
                    drawdown_stability_score,
                    regime_score,
                    overfitting_score,
                    stress_score,
                ]
            )
            / 6.0
        )

        conclusions = self._conclusions(metrics_summary, validation_summary_data, risk_report_data)

        return ResearchReport(
            experiment_metadata=experiment_metadata,
            metrics_summary=metrics_summary,
            validation_summary=validation_summary_data,
            equity_review=equity_review_data,
            risk_report=risk_report_data,
            confidence_score=round(confidence_score, 2),
            conclusions=conclusions,
        )
