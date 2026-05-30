from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class StrategyLifecycleState(str, Enum):
    """Lifecycle states for a strategy through the Research Division and beyond."""

    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    BACKTESTING = "backtesting"
    VALIDATION = "validation"
    PAPER_TRADING = "paper_trading"
    LIVE_ELIGIBLE = "live_eligible"
    DEPLOYED = "deployed"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class StrategyDNA(BaseModel):
    """Immutable strategy definition with versioned lifecycle tracking.

    Represents a single strategy instance throughout its entire lifecycle.
    Every state transition is recorded in the database via the updated_at field
    and an accompanying entry in council_decisions.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this strategy version."""

    name: str
    """Human-readable name of the strategy (e.g. 'EMA Crossover - NIFTY 15min')."""

    version: int = Field(default=1, ge=1)
    """Version number. Increments when strategy logic changes."""

    lifecycle_state: StrategyLifecycleState = Field(
        default=StrategyLifecycleState.DRAFT
    )
    """Current position in the strategy lifecycle state machine."""

    definition_json: dict[str, Any] = Field(default_factory=dict)
    """Strategy logic definition — parameters, entry/exit rules, filters.

    Structure is strategy-specific. Contents are validated by the Research
    Factory pipeline, not by this model.
    """

    risk_controls_json: dict[str, Any] = Field(default_factory=dict)
    """Risk control parameters required for Live Eligible certification.

    Includes: position_sizing, max_drawdown, daily_loss_limit,
    regime_restrictions, correlation_ceiling, time_in_force.
    """

    created_at: datetime = Field(default_factory=datetime.utcnow)
    """Timestamp when this strategy version was first created."""

    updated_at: datetime = Field(default_factory=datetime.utcnow)
    """Timestamp of the last state transition or modification."""

    def transition_to(self, new_state: StrategyLifecycleState) -> None:
        """Advance the strategy to a new lifecycle state.

        Validates that the transition follows the expected order.
        Raises ValueError for invalid transitions.

        This is a lightweight domain check. Full gate logic lives in services.
        """
        allowed_transitions = {
            StrategyLifecycleState.DRAFT: [StrategyLifecycleState.UNDER_REVIEW],
            StrategyLifecycleState.UNDER_REVIEW: [
                StrategyLifecycleState.BACKTESTING,
                StrategyLifecycleState.DRAFT,
            ],
            StrategyLifecycleState.BACKTESTING: [
                StrategyLifecycleState.VALIDATION,
                StrategyLifecycleState.UNDER_REVIEW,
            ],
            StrategyLifecycleState.VALIDATION: [
                StrategyLifecycleState.PAPER_TRADING,
                StrategyLifecycleState.UNDER_REVIEW,
            ],
            StrategyLifecycleState.PAPER_TRADING: [
                StrategyLifecycleState.LIVE_ELIGIBLE,
                StrategyLifecycleState.UNDER_REVIEW,
            ],
            StrategyLifecycleState.LIVE_ELIGIBLE: [
                StrategyLifecycleState.DEPLOYED,
                StrategyLifecycleState.UNDER_REVIEW,
            ],
            StrategyLifecycleState.DEPLOYED: [
                StrategyLifecycleState.SUSPENDED,
                StrategyLifecycleState.RETIRED,
            ],
            StrategyLifecycleState.SUSPENDED: [
                StrategyLifecycleState.DEPLOYED,
                StrategyLifecycleState.RETIRED,
            ],
            StrategyLifecycleState.RETIRED: [],
        }

        allowed = allowed_transitions.get(self.lifecycle_state, [])
        if new_state not in allowed:
            raise ValueError(
                f"Cannot transition from {self.lifecycle_state.value} to "
                f"{new_state.value}. Allowed: {[s.value for s in allowed]}"
            )

        self.lifecycle_state = new_state
        self.updated_at = datetime.utcnow()

    class Config:
        use_enum_values = False
        """Keep enum values as Enum instances in Python; serialise to strings."""