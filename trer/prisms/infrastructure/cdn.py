"""Critical Dependency Node utilities for the infrastructure prism.

The CDN model ranks unresolved pressure at high-flow civic/industrial/residential
nodes. It does not predict failure directly. Scores are triage signals for
where to enrich evidence next.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Literal, Optional

NodeClass = Literal[
    "housing",
    "medical",
    "transit",
    "civic",
    "education",
    "industrial",
    "retail",
]

Confidence = Literal["low", "medium", "high"]

VALID_NODE_CLASSES: set[str] = {
    "housing",
    "medical",
    "transit",
    "civic",
    "education",
    "industrial",
    "retail",
}


@dataclass(frozen=True)
class CriticalDependencyNode:
    """JSON-compatible packet for Critical Dependency Observatory indexing."""

    node_id: str
    name: str
    city: str
    address: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    node_class: NodeClass = "civic"
    place_types: list[str] = field(default_factory=list)
    static_dependency_density: Optional[float] = None
    dynamic_flow_density: Optional[float] = None
    consequence_density: Optional[float] = None
    dissipation_capacity: Optional[float] = None
    pressure_mismatch_score: Optional[float] = None
    review_count: Optional[int] = None
    rating: Optional[float] = None
    nearby_transit_count: Optional[int] = None
    nearby_parking_count: Optional[int] = None
    nearby_services_count: Optional[int] = None
    known_public_records: list[str] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)
    confidence: Confidence = "low"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CriticalDependencyNode":
        node_class = data.get("node_class", "civic")
        if node_class not in VALID_NODE_CLASSES:
            raise ValueError(f"invalid node_class: {node_class!r}")
        return cls(
            node_id=str(data.get("node_id", "")),
            name=str(data.get("name", "")),
            city=str(data.get("city", "")),
            address=str(data.get("address", "")),
            lat=data.get("lat"),
            lng=data.get("lng"),
            node_class=node_class,  # type: ignore[arg-type]
            place_types=list(data.get("place_types", [])),
            static_dependency_density=data.get("static_dependency_density"),
            dynamic_flow_density=data.get("dynamic_flow_density"),
            consequence_density=data.get("consequence_density"),
            dissipation_capacity=data.get("dissipation_capacity"),
            pressure_mismatch_score=data.get("pressure_mismatch_score"),
            review_count=data.get("review_count"),
            rating=data.get("rating"),
            nearby_transit_count=data.get("nearby_transit_count"),
            nearby_parking_count=data.get("nearby_parking_count"),
            nearby_services_count=data.get("nearby_services_count"),
            known_public_records=list(data.get("known_public_records", [])),
            source_urls=list(data.get("source_urls", [])),
            confidence=data.get("confidence", "low"),  # type: ignore[arg-type]
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clamp_0_1(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_pressure_mismatch_score(
    *,
    static_dependency_density: Optional[float],
    dynamic_flow_density: Optional[float],
    consequence_density: Optional[float],
    dissipation_capacity: Optional[float],
) -> Optional[float]:
    """Compute unresolved pressure when enough normalized evidence exists.

    Inputs are expected to be normalized 0..1 values. Unknown dissipation is not
    treated as weak by default; it should lower confidence and trigger evidence
    enrichment rather than automatically inflate risk.
    """

    required = [
        static_dependency_density,
        dynamic_flow_density,
        consequence_density,
        dissipation_capacity,
    ]
    if any(value is None for value in required):
        return None

    static, dynamic, consequence, dissipation = (_clamp_0_1(float(v)) for v in required)  # type: ignore[arg-type]
    pressure = (static + dynamic + consequence) / 3.0
    return round(_clamp_0_1(pressure - dissipation), 4)


def enrich_pressure_score(node: CriticalDependencyNode) -> CriticalDependencyNode:
    """Return a copy with pressure_mismatch_score filled when possible."""

    if node.pressure_mismatch_score is not None:
        return node
    score = compute_pressure_mismatch_score(
        static_dependency_density=node.static_dependency_density,
        dynamic_flow_density=node.dynamic_flow_density,
        consequence_density=node.consequence_density,
        dissipation_capacity=node.dissipation_capacity,
    )
    return CriticalDependencyNode(**{**node.to_dict(), "pressure_mismatch_score": score})


def node_text_summary(node: CriticalDependencyNode) -> str:
    """Convert a CDN packet to text suitable for embeddings/search."""

    fields = [
        f"Critical dependency node: {node.name}",
        f"City: {node.city}",
        f"Address: {node.address}",
        f"Class: {node.node_class}",
        f"Place types: {', '.join(node.place_types) if node.place_types else 'unknown'}",
        f"Static dependency density: {node.static_dependency_density}",
        f"Dynamic flow density: {node.dynamic_flow_density}",
        f"Consequence density: {node.consequence_density}",
        f"Dissipation capacity: {node.dissipation_capacity}",
        f"Pressure mismatch score: {node.pressure_mismatch_score}",
        f"Google-derived proxies: reviews={node.review_count}, rating={node.rating}",
        (
            "Nearby context: "
            f"transit={node.nearby_transit_count}, "
            f"parking={node.nearby_parking_count}, "
            f"services={node.nearby_services_count}"
        ),
        f"Known public records: {', '.join(node.known_public_records) if node.known_public_records else 'not enriched'}",
        f"Confidence: {node.confidence}",
    ]
    return "\n".join(fields)


def rank_flow_first(nodes: Iterable[CriticalDependencyNode]) -> list[CriticalDependencyNode]:
    """Rank nodes by flow concentration before unresolved-pressure tie-breakers."""

    enriched = [enrich_pressure_score(node) for node in nodes]

    def key(node: CriticalDependencyNode) -> tuple[float, float, float, float]:
        return (
            node.dynamic_flow_density if node.dynamic_flow_density is not None else -1.0,
            node.pressure_mismatch_score if node.pressure_mismatch_score is not None else -1.0,
            node.static_dependency_density if node.static_dependency_density is not None else -1.0,
            node.consequence_density if node.consequence_density is not None else -1.0,
        )

    return sorted(enriched, key=key, reverse=True)
