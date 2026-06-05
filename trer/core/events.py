"""Core event types.

Events are reconstructed state changes. Pressure, ambiguity, and dissipation can
be expressed later as event kinds or prism-level annotations; the core only
requires evidence-linked transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Event:
    """An inferred event reconstructed from observations."""

    id: str
    kind: str
    entity_id: str
    start_at: str
    end_at: str
    evidence: tuple[str, ...]
    attributes: dict[str, Any] = field(default_factory=dict)
