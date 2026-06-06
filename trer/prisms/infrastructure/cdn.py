"""Critical Dependency Node utilities for the infrastructure prism.

The CDN model ranks unresolved pressure at high-flow civic/industrial/residential
nodes. It does not predict failure directly. Scores are triage signals for
where to enrich evidence next.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
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
RankMode = Literal["flow", "criticality"]

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
    criticality_score: Optional[float] = None
    pressure_mismatch_score: Optional[float] = None
    pressure_confidence: Confidence = "low"
    dissipation_confidence: Confidence = "low"
    review_count: Optional[int] = None
    rating: Optional[float] = None
    nearby_transit_count: Optional[int] = None
    nearby_parking_count: Optional[int] = None
    nearby_services_count: Optional[int] = None
    flow_sources: dict[str, Any] = field(default_factory=dict)
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
            criticality_score=data.get("criticality_score"),
            pressure_mismatch_score=data.get("pressure_mismatch_score"),
            pressure_confidence=data.get("pressure_confidence", "low"),  # type: ignore[arg-type]
            dissipation_confidence=data.get("dissipation_confidence", "low"),  # type: ignore[arg-type]
            review_count=data.get("review_count"),
            rating=data.get("rating"),
            nearby_transit_count=data.get("nearby_transit_count"),
            nearby_parking_count=data.get("nearby_parking_count"),
            nearby_services_count=data.get("nearby_services_count"),
            flow_sources=dict(data.get("flow_sources", {})),
            known_public_records=list(data.get("known_public_records", [])),
            source_urls=list(data.get("source_urls", [])),
            confidence=data.get("confidence", "low"),  # type: ignore[arg-type]
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clamp_0_1(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_criticality_score(
    *,
    static_dependency_density: Optional[float],
    dynamic_flow_density: Optional[float],
    consequence_density: Optional[float],
) -> Optional[float]:
    """Compute concentrated node criticality from normalized 0..1 signals.

    This intentionally excludes dissipation. It answers: how concentrated is the
    node's load/consequence profile before asking whether that pressure is being
    relieved?
    """

    required = [static_dependency_density, dynamic_flow_density, consequence_density]
    if any(value is None for value in required):
        return None
    static, dynamic, consequence = (_clamp_0_1(float(v)) for v in required)  # type: ignore[arg-type]
    return round(static * dynamic * consequence, 4)


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


def infer_pressure_confidence(node: CriticalDependencyNode) -> Confidence:
    """Infer coarse confidence from available scoring evidence."""

    known_core = sum(
        value is not None
        for value in [
            node.static_dependency_density,
            node.dynamic_flow_density,
            node.consequence_density,
        ]
    )
    if known_core == 3 and node.dissipation_capacity is not None:
        return "medium" if not node.known_public_records else "high"
    if known_core >= 2:
        return "low"
    return "low"


def enrich_scores(node: CriticalDependencyNode) -> CriticalDependencyNode:
    """Return a copy with derived scores and confidence fields filled."""

    criticality = node.criticality_score
    if criticality is None:
        criticality = compute_criticality_score(
            static_dependency_density=node.static_dependency_density,
            dynamic_flow_density=node.dynamic_flow_density,
            consequence_density=node.consequence_density,
        )

    pressure = node.pressure_mismatch_score
    if pressure is None:
        pressure = compute_pressure_mismatch_score(
            static_dependency_density=node.static_dependency_density,
            dynamic_flow_density=node.dynamic_flow_density,
            consequence_density=node.consequence_density,
            dissipation_capacity=node.dissipation_capacity,
        )

    return CriticalDependencyNode(
        **{
            **node.to_dict(),
            "criticality_score": criticality,
            "pressure_mismatch_score": pressure,
            "pressure_confidence": node.pressure_confidence or infer_pressure_confidence(node),
            "dissipation_confidence": node.dissipation_confidence,
        }
    )


def enrich_pressure_score(node: CriticalDependencyNode) -> CriticalDependencyNode:
    """Backward-compatible alias for deriving CDN scores."""

    return enrich_scores(node)


def node_text_summary(node: CriticalDependencyNode) -> str:
    """Convert a CDN packet to text suitable for embeddings/search."""

    flow_sources = node.flow_sources or {
        "google_reviews": node.review_count,
        "nearby_transit": node.nearby_transit_count,
        "nearby_parking": node.nearby_parking_count,
        "nearby_services": node.nearby_services_count,
    }
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
        f"Criticality score: {node.criticality_score}",
        f"Pressure mismatch score: {node.pressure_mismatch_score}",
        f"Pressure confidence: {node.pressure_confidence}",
        f"Dissipation confidence: {node.dissipation_confidence}",
        f"Google-derived proxies: reviews={node.review_count}, rating={node.rating}",
        f"Flow sources: {json.dumps(flow_sources, sort_keys=True)}",
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

    enriched = [enrich_scores(node) for node in nodes]

    def key(node: CriticalDependencyNode) -> tuple[float, float, float, float, float]:
        return (
            node.dynamic_flow_density if node.dynamic_flow_density is not None else -1.0,
            node.criticality_score if node.criticality_score is not None else -1.0,
            node.pressure_mismatch_score if node.pressure_mismatch_score is not None else -1.0,
            node.static_dependency_density if node.static_dependency_density is not None else -1.0,
            node.consequence_density if node.consequence_density is not None else -1.0,
        )

    return sorted(enriched, key=key, reverse=True)


def rank_criticality_first(nodes: Iterable[CriticalDependencyNode]) -> list[CriticalDependencyNode]:
    """Rank nodes by concentrated load/consequence before raw flow."""

    enriched = [enrich_scores(node) for node in nodes]

    def key(node: CriticalDependencyNode) -> tuple[float, float, float, float]:
        unknown_dissipation = 1.0 if node.dissipation_capacity is None else 0.0
        return (
            node.criticality_score if node.criticality_score is not None else -1.0,
            unknown_dissipation,
            node.pressure_mismatch_score if node.pressure_mismatch_score is not None else -1.0,
            node.dynamic_flow_density if node.dynamic_flow_density is not None else -1.0,
        )

    return sorted(enriched, key=key, reverse=True)


def load_nodes(path: Path) -> list[CriticalDependencyNode]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError("CDN fixture must be a JSON list of packets")
    return [CriticalDependencyNode.from_dict(item) for item in raw]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the TRER infrastructure CDN prism over JSON packets.")
    parser.add_argument("packet_json", type=Path, help="Path to a JSON list of CDN packets.")
    parser.add_argument(
        "--rank",
        choices=["flow", "criticality"],
        default="flow",
        help="Ranking mode. 'flow' preserves discovery bias; 'criticality' surfaces load/consequence concentration.",
    )
    args = parser.parse_args(argv)

    nodes = load_nodes(args.packet_json)
    ranked = rank_flow_first(nodes) if args.rank == "flow" else rank_criticality_first(nodes)
    for node in ranked:
        print("=" * 80)
        print(node_text_summary(node))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
