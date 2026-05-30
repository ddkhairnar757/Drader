from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class CouncilDecisionType(str, Enum):
    """Canonical Council decision types for the entire Drader system.

    Encompasses outcomes for gate decisions (approve, reject, revise, defer),
    pipeline experiment outcomes (proceed, abandon), and pending state.
    """

    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"
    DEFER = "defer"
    PROCEED = "proceed"
    ABANDON = "abandon"
    PENDING = "pending"


class CouncilDecision(BaseModel):
    """Structured record of an AI Council deliberation.

    Captures every Council vote, the individual agent votes, the
    Founder's final decision (including overrides), and the rationale.
    These records form the institutional audit trail of how and why
    research decisions were made.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this decision record."""

    session_id: str
    """Identifier grouping related Council deliberations in a single session."""

    strategy_id: Optional[str] = None
    """Reference to the StrategyDNA this decision pertains to, if applicable."""

    decision_type: CouncilDecisionType
    """The outcome of this Council deliberation."""

    votes_json: dict[str, Any] = Field(default_factory=dict)
    """Individual agent votes and positions.

    Structure: {'agent_name': {'vote': 'approve|reject|abstain',
    'rationale': '...'}, ...}
    """

    founder_override: bool = Field(default=False)
    """Whether the Founder overrode the Council's recommendation."""

    rationale: str = Field(default="")
    """Plain-English explanation of the decision, including override reasons
    if applicable."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    """Timestamp when the decision was recorded."""

    updated_at: datetime = Field(default_factory=datetime.utcnow)
    """Timestamp of the last update to this record."""

    class Config:
        use_enum_values = False
