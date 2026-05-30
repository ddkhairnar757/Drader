from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryCategory(str, Enum):
    """Categories for system memory records."""

    CONFIGURATION = "configuration"
    GOVERNANCE = "governance"
    WORKFLOW = "workflow"
    PREFERENCE = "preference"
    CHECKPOINT = "checkpoint"


class SystemMemory(BaseModel):
    """Internal system state record.

    Stores workspace configurations, user preferences, pipeline status,
    governance snapshots, and workflow checkpoints. Unlike the DNA tables,
    system_memory records are mutable — they reflect the current state
    of the Drader OS environment.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this memory record."""

    memory_key: str
    """Unique key for this memory value (e.g. 'workspace.active_layout')."""

    memory_value: str
    """Value stored as a JSON-serialised string for flexibility."""

    category: MemoryCategory
    """Classification of this memory record."""

    description: str = Field(default="")
    """Human-readable description of what this memory record holds."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    """Timestamp when this record was created."""

    updated_at: datetime = Field(default_factory=datetime.utcnow)
    """Timestamp of the last update to this record."""

    class Config:
        use_enum_values = False