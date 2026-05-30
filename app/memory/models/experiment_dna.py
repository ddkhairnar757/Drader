from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.memory.models.council_decisions import CouncilDecisionType


class ExperimentStage(str, Enum):
    """Stages of the Research Factory pipeline."""

    RESEARCH = "research"
    BACKTESTING = "backtesting"
    VALIDATION = "validation"
    PAPER_TRADING = "paper_trading"
    REPORTS = "reports"


class ExperimentDNA(BaseModel):
    """Record of a single run through a Research Factory pipeline stage.

    Every backtest, validation run, or paper-trading session creates one
    ExperimentDNA record. The record captures the hypothesis, parameters,
    results, and the Council's gate decision.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this experiment run."""

    strategy_id: str
    """Reference to the StrategyDNA this experiment belongs to."""

    stage: ExperimentStage
    """Which pipeline stage this experiment represents."""

    hypothesis: str
    """Falsifiable statement being tested. Written before any parameters are set."""

    parameters_json: dict[str, Any] = Field(default_factory=dict)
    """Strategy parameters used for this specific run. Pre-registered before execution."""

    results_json: dict[str, Any] = Field(default_factory=dict)
    """Output metrics, performance data, and logs from the run."""

    council_decision: CouncilDecisionType = Field(default=CouncilDecisionType.PENDING)
    """Council's gate decision after reviewing this experiment."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    """Timestamp when the experiment was initiated."""

    updated_at: datetime = Field(default_factory=datetime.utcnow)
    """Timestamp of the last update to this record."""

    class Config:
        use_enum_values = False
