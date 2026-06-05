"""Core data structures for deterministic temporal reconstruction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

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


@dataclass(frozen=True)
class Event:
    """An inferred event reconstructed from observations."""

    id: str
    kind: Literal["movement"]
    entity_id: str
    start_at: str
    end_at: str
    evidence: tuple[str, ...]
    attributes: dict[str, Any] = field(default_factory=dict)


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


@dataclass(frozen=True)
class Hypothesis:
    """A candidate explanation awaiting acceptance/rejection."""

    id: str
    claim: str
    evidence: tuple[str, ...]
    status: Literal["candidate", "accepted", "rejected"] = "candidate"
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Timeline:
    """Deterministic reconstruction output."""

    entities: tuple[Entity, ...]
    observations: tuple[Observation, ...]
    events: tuple[Event, ...]
    relationships: tuple[Relationship, ...] = ()
    hypotheses: tuple[Hypothesis, ...] = ()
