"""Deterministic reconstruction loop for plain JSON-compatible observations."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .events import Event
from .nodes import Entity, Observation
from .timelines import Timeline


def reconstruct_timeline(payload: dict[str, Any] | Iterable[dict[str, Any]]) -> Timeline:
    """Reconstruct a minimal timeline from JSON-compatible observations.

    The first invariant is intentionally small: if the same entity is observed at
    two different locations over time, emit one deterministic movement event.
    """

    observations = _parse_observations(payload)
    entities = _derive_entities(observations)
    events = _derive_movement_events(observations)
    return Timeline(
        entities=tuple(entities),
        observations=tuple(observations),
        events=tuple(events),
    )


def _parse_observations(payload: dict[str, Any] | Iterable[dict[str, Any]]) -> list[Observation]:
    if isinstance(payload, dict):
        raw_observations = payload.get("observations", [])
    else:
        raw_observations = list(payload)

    observations: list[Observation] = []
    for item in raw_observations:
        raw_location = item.get("location")
        location = tuple(raw_location) if raw_location is not None else None
        if location is not None and len(location) != 2:
            raise ValueError(f"Observation {item.get('id', '<unknown>')} has invalid location")

        observations.append(
            Observation(
                id=str(item["id"]),
                entity_id=str(item["entity_id"]),
                observed_at=str(item["observed_at"]),
                location=location,  # type: ignore[arg-type]
                label=item.get("label"),
                confidence=item.get("confidence"),
                source=item.get("source"),
                attributes=dict(item.get("attributes", {})),
            )
        )

    return sorted(observations, key=lambda observation: (observation.observed_at, observation.id))


def _derive_entities(observations: list[Observation]) -> list[Entity]:
    labels: dict[str, str] = {}
    for observation in observations:
        labels.setdefault(observation.entity_id, observation.label or observation.entity_id)
    return [Entity(id=entity_id, label=labels[entity_id]) for entity_id in sorted(labels)]


def _derive_movement_events(observations: list[Observation]) -> list[Event]:
    by_entity: dict[str, list[Observation]] = defaultdict(list)
    for observation in observations:
        if observation.location is not None:
            by_entity[observation.entity_id].append(observation)

    events: list[Event] = []
    for entity_id in sorted(by_entity):
        entity_observations = sorted(by_entity[entity_id], key=lambda item: (item.observed_at, item.id))
        for previous, current in zip(entity_observations, entity_observations[1:]):
            if previous.location == current.location:
                continue
            events.append(
                Event(
                    id=f"event:movement:{entity_id}:{previous.id}->{current.id}",
                    kind="movement",
                    entity_id=entity_id,
                    start_at=previous.observed_at,
                    end_at=current.observed_at,
                    evidence=(previous.id, current.id),
                    attributes={
                        "from": previous.location,
                        "to": current.location,
                    },
                )
            )

    return events
