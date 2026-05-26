from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ExperimentRecord:
    experiment_id: str
    name: str
    strategy: str
    dataset: str
    timeframe: str
    brokerage: float
    slippage: float
    start_time: datetime
    end_time: datetime | None = None
    settings: dict[str, float] | None = None
    parameters: dict[str, float] | None = None
    metrics: dict[str, float] | None = None
    equity_curve_path: str | None = None
    notes: str | None = None

    def complete(self, metrics: dict[str, float]) -> None:
        self.end_time = datetime.now(timezone.utc)
        self.metrics = metrics

    def to_dict(self) -> dict[str, object | None]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "strategy": self.strategy,
            "dataset": self.dataset,
            "timeframe": self.timeframe,
            "brokerage": self.brokerage,
            "slippage": self.slippage,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "settings": self.settings,
            "parameters": self.parameters,
            "metrics": self.metrics,
            "equity_curve_path": self.equity_curve_path,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object | None]) -> "ExperimentRecord":
        return cls(
            experiment_id=str(data["experiment_id"]),
            name=str(data["name"]),
            strategy=str(data["strategy"]),
            dataset=str(data["dataset"]),
            timeframe=str(data["timeframe"]),
            brokerage=float(data["brokerage"]),
            slippage=float(data["slippage"]),
            start_time=datetime.fromisoformat(str(data["start_time"])),
            end_time=datetime.fromisoformat(str(data["end_time"])) if data.get("end_time") else None,
            settings=data.get("settings") if isinstance(data.get("settings"), dict) else None,
            parameters=data.get("parameters") if isinstance(data.get("parameters"), dict) else None,
            metrics=data.get("metrics") if isinstance(data.get("metrics"), dict) else None,
            equity_curve_path=str(data["equity_curve_path"]) if data.get("equity_curve_path") else None,
            notes=str(data["notes"]) if data.get("notes") else None,
        )

    def save_to_json(self, file_path: Path | str) -> None:
        file_path = Path(file_path)
        with file_path.open("w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2)
