from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .experiment import ExperimentRecord


class ExperimentPersistence:
    def __init__(self, base_path: Path | str = "experiments/storage") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_experiment(
        self,
        record: ExperimentRecord,
        equity_curve: pd.DataFrame,
    ) -> Path:
        if equity_curve.empty:
            raise ValueError("Equity curve data cannot be empty.")

        experiment_dir = self.base_path / record.experiment_id
        if experiment_dir.exists():
            raise FileExistsError(f"Experiment already exists: {record.experiment_id}")
        experiment_dir.mkdir(parents=True, exist_ok=False)

        equity_path = experiment_dir / "equity_curve.csv"
        equity_curve.to_csv(equity_path, index=True)
        record.equity_curve_path = str(equity_path)

        json_path = experiment_dir / "experiment.json"
        record.save_to_json(json_path)
        return experiment_dir

    def load_experiment(self, json_path: Path | str) -> ExperimentRecord:
        json_path = Path(json_path)
        with json_path.open("r", encoding="utf-8") as handle:
            content = json.load(handle)
        return ExperimentRecord.from_dict(content)

    def list_experiments(self) -> list[Path]:
        return sorted([path for path in self.base_path.iterdir() if path.is_dir()])
