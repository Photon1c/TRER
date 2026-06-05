"""Core node types.

Nodes are durable things TRER can reason about across time. The core keeps
this deliberately plain: entities and observations, not domain-specific actors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Location = tuple[float, float]


@dataclass(frozen=True)
class Entity:
    """A durable thing observed over time."""

    id: str
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Observation:
    """A timestamped observation of an entity."""

    id: str
    entity_id: str
    observed_at: str
    location: Location | None = None
    label: str | None = None
    confidence: float | None = None
    source: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
