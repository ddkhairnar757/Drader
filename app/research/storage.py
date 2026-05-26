from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from experiments.experiment import ExperimentRecord
from experiments.persistence import ExperimentPersistence


class ExperimentStorage:
    def __init__(self, base_path: Path | str = "experiments/storage") -> None:
        self.persistence = ExperimentPersistence(base_path=base_path)

    @property
    def base_path(self) -> Path:
        return self.persistence.base_path

    def save(self, record: ExperimentRecord, equity_curve: pd.DataFrame) -> Path:
        record.end_time = datetime.now(timezone.utc)
        return self.persistence.save_experiment(record, equity_curve)

    def load_by_id(self, experiment_id: str) -> ExperimentRecord | None:
        for path in self.persistence.list_experiments():
            json_path = path / "experiment.json"
            if not json_path.exists():
                continue
            record = self.persistence.load_experiment(json_path)
            if record.experiment_id == experiment_id:
                return record
        return None

    def list_all(self) -> list[ExperimentRecord]:
        experiments: list[ExperimentRecord] = []
        for path in self.persistence.list_experiments():
            json_path = path / "experiment.json"
            if not json_path.exists():
                continue
            experiments.append(self.persistence.load_experiment(json_path))
        return sorted(experiments, key=lambda exp: exp.start_time)

    def find_by_strategy(self, strategy_name: str) -> list[ExperimentRecord]:
        return [exp for exp in self.list_all() if exp.strategy == strategy_name]

    def filter_by_date(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[ExperimentRecord]:
        results = self.list_all()
        if start is not None:
            results = [exp for exp in results if exp.start_time >= start]
        if end is not None:
            results = [exp for exp in results if exp.start_time <= end]
        return results

    def filter_by_metric(
        self,
        metric_name: str,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> list[ExperimentRecord]:
        results: list[ExperimentRecord] = []
        for exp in self.list_all():
            if exp.metrics is None or metric_name not in exp.metrics:
                continue
            value = float(exp.metrics[metric_name])
            if min_value is not None and value < min_value:
                continue
            if max_value is not None and value > max_value:
                continue
            results.append(exp)
        return results
