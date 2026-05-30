from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FailureDNA(BaseModel):
    """Post-mortem record of a stopped or abandoned strategy.

    Every strategy that is retired, abandoned during pipeline review, or
    suspended from paper trading generates a FailureDNA record.
    Documented failure is institutional capital — the Knowledge Graph
    indexes these records so future research can learn from them.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this failure record."""

    strategy_id: str
    """Reference to the StrategyDNA that failed."""

    experiment_id: str
    """Reference to the ExperimentDNA run where failure was identified."""

    failure_reason: str
    """Plain-English explanation of why the strategy stopped or was abandoned."""

    council_dissent_json: dict[str, Any] = Field(default_factory=dict)
    """Structured record of Council opposition briefs and dissenting votes."""

    lessons_learned: str = Field(default="")
    """Lessons extracted from this failure for future institutional reference."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    """Timestamp when the failure was recorded."""

    updated_at: datetime = Field(default_factory=datetime.utcnow)
    """Timestamp of the last update to this record."""

    class Config:
        use_enum_values = False