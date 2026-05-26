from __future__ import annotations

from pathlib import Path

import pandas as pd


class MetricsDashboard:
    @staticmethod
    def create_summary(metrics: dict[str, float]) -> pd.DataFrame:
        if not metrics:
            raise ValueError("Metrics dictionary cannot be empty.")
        return pd.DataFrame(list(metrics.items()), columns=["metric", "value"])

    @staticmethod
    def save_summary(
        metrics: dict[str, float],
        save_path: Path | str,
    ) -> pd.DataFrame:
        summary = MetricsDashboard.create_summary(metrics)
        summary.to_csv(Path(save_path), index=False)
        return summary

    @staticmethod
    def print_summary(metrics: dict[str, float]) -> None:
        summary = MetricsDashboard.create_summary(metrics)
        print(summary.to_string(index=False))
        return summary
