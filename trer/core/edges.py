"""Core edge types.

Edges connect nodes through relationships. Domain interpretations belong in
prisms; the core stores the relationship and its evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Relationship:
    """A relationship inferred between entities."""

    id: str
    kind: str
    subject_id: str
    object_id: str
    observed_at: str
    evidence: tuple[str, ...]
    attributes: dict[str, Any] = field(default_factory=dict)
