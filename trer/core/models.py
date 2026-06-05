"""Backward-compatible imports for core data structures.

The core layout is intentionally split into nodes, edges, events, and timelines.
This module keeps the early `trer.core.models` import path stable.
"""

from .edges import Relationship
from .events import Event
from .nodes import Entity, Location, Observation
from .timelines import Hypothesis, Timeline

__all__ = [
    "Entity",
    "Event",
    "Hypothesis",
    "Location",
    "Observation",
    "Relationship",
    "Timeline",
]
