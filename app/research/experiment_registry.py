from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.research.storage import ExperimentStorage
from experiments.experiment import ExperimentRecord


class ExperimentRegistry:
    def __init__(self, storage: ExperimentStorage | None = None) -> None:
        self.storage = storage or ExperimentStorage()

    def list_experiments(self) -> list[ExperimentRecord]:
        return self.storage.list_all()

    def get_experiment(self, experiment_id: str) -> ExperimentRecord | None:
        return self.storage.load_by_id(experiment_id)

    def search_by_strategy(self, strategy_name: str) -> list[ExperimentRecord]:
        return [exp for exp in self.list_experiments() if exp.strategy == strategy_name]

    def filter_by_date(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[ExperimentRecord]:
        results = self.list_experiments()
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
        for exp in self.list_experiments():
            if exp.metrics is None or metric_name not in exp.metrics:
                continue
            value = float(exp.metrics[metric_name])
            if min_value is not None and value < min_value:
                continue
            if max_value is not None and value > max_value:
                continue
            results.append(exp)
        return results
