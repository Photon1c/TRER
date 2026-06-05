"""Core timeline and hypothesis containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .edges import Relationship
from .events import Event
from .nodes import Entity, Observation


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
