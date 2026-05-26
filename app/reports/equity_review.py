from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class EquityReviewSummary:
    total_periods: int
    volatility: float
    smoothness_score: float
    max_drawdown: float
    drawdown_cluster_count: int
    average_drawdown_duration: float
    worst_drawdown_duration: int
    recovery_score: float


class EquityReview:
    @staticmethod
    def _drawdown_clusters(drawdown: pd.Series) -> tuple[int, float, int]:
        cluster_lengths: list[int] = []
        current_length = 0
        for is_drawdown in drawdown < 0:
            if is_drawdown:
                current_length += 1
            elif current_length > 0:
                cluster_lengths.append(current_length)
                current_length = 0
        if current_length > 0:
            cluster_lengths.append(current_length)

        if not cluster_lengths:
            return 0, 0.0, 0

        return (
            len(cluster_lengths),
            float(np.mean(cluster_lengths)),
            int(max(cluster_lengths)),
        )

    @staticmethod
    def analyze(equity_curve: pd.DataFrame) -> EquityReviewSummary:
        if "equity" not in equity_curve.columns:
            raise ValueError("Equity curve must contain an 'equity' column.")

        values = equity_curve["equity"].astype(float)
        returns = values.pct_change().fillna(0.0)
        volatility = float(returns.std(ddof=0))
        smoothness_score = float(np.clip(10.0 / (1.0 + volatility * 10.0), 0.0, 10.0))

        cumulative_high = values.cummax()
        drawdown = (values - cumulative_high) / cumulative_high
        max_drawdown = float(drawdown.min())

        cluster_count, avg_duration, worst_duration = EquityReview._drawdown_clusters(drawdown)
        recovery_score = float(np.clip(10.0 * (1.0 - min(1.0, abs(max_drawdown) / 0.5)), 0.0, 10.0))

        return EquityReviewSummary(
            total_periods=len(values),
            volatility=volatility,
            smoothness_score=smoothness_score,
            max_drawdown=max_drawdown,
            drawdown_cluster_count=cluster_count,
            average_drawdown_duration=avg_duration,
            worst_drawdown_duration=worst_duration,
            recovery_score=recovery_score,
        )
