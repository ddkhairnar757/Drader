from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class RiskReportSummary:
    max_drawdown: float
    tail_risk_5: float
    tail_risk_1: float
    max_consecutive_loss_days: int
    loss_concentration: float
    capital_stress_score: float


class RiskReport:
    @staticmethod
    def _max_consecutive_negative_returns(returns: pd.Series) -> int:
        longest = 0
        current = 0
        for value in returns:
            if value < 0:
                current += 1
                longest = max(longest, current)
            else:
                current = 0
        return longest

    @staticmethod
    def _loss_concentration(returns: pd.Series) -> float:
        losses = -returns[returns < 0]
        if losses.empty:
            return 0.0
        total_loss = float(losses.sum())
        worst_losses = float(losses.quantile(0.9))
        return float(np.clip(worst_losses / (total_loss + 1e-9), 0.0, 1.0))

    @staticmethod
    def analyze(equity_curve: pd.DataFrame) -> RiskReportSummary:
        if "equity" not in equity_curve.columns:
            raise ValueError("Equity curve must contain an 'equity' column.")

        values = equity_curve["equity"].astype(float)
        returns = values.pct_change().fillna(0.0)
        negative_returns = returns[returns < 0]

        tail_risk_5 = float(np.percentile(returns, 5)) if len(returns) > 0 else 0.0
        tail_risk_1 = float(np.percentile(returns, 1)) if len(returns) > 0 else 0.0
        max_consecutive_loss_days = RiskReport._max_consecutive_negative_returns(returns)
        loss_concentration = RiskReport._loss_concentration(returns)

        cumulative_high = values.cummax()
        drawdown = (values - cumulative_high) / cumulative_high
        max_drawdown = float(drawdown.min())
        capital_stress_score = float(np.clip(10.0 * (1.0 - min(1.0, abs(max_drawdown) / 0.5)), 0.0, 10.0))

        return RiskReportSummary(
            max_drawdown=max_drawdown,
            tail_risk_5=tail_risk_5,
            tail_risk_1=tail_risk_1,
            max_consecutive_loss_days=max_consecutive_loss_days,
            loss_concentration=loss_concentration,
            capital_stress_score=capital_stress_score,
        )
