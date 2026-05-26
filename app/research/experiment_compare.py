from __future__ import annotations

import pandas as pd

from experiments.experiment import ExperimentRecord


def compare_experiments(a: ExperimentRecord, b: ExperimentRecord) -> pd.DataFrame:
    metrics_a = pd.Series(a.metrics or {}, name=a.experiment_id)
    metrics_b = pd.Series(b.metrics or {}, name=b.experiment_id)
    comparison = pd.concat([metrics_a, metrics_b], axis=1)
    comparison.columns = [a.name, b.name]
    return comparison


def compare_equity_curves(a: ExperimentRecord, b: ExperimentRecord) -> pd.DataFrame:
    if not a.equity_curve_path or not b.equity_curve_path:
        raise ValueError("Both experiments must include equity curve paths.")

    curve_a = pd.read_csv(a.equity_curve_path, index_col=0, parse_dates=True)
    curve_b = pd.read_csv(b.equity_curve_path, index_col=0, parse_dates=True)
    curve_a = curve_a.rename(columns={curve_a.columns[0]: a.name})
    curve_b = curve_b.rename(columns={curve_b.columns[0]: b.name})
    return pd.concat([curve_a, curve_b], axis=1)
