"""Infrastructure prism for dependency, maintenance, and pressure analysis."""

__all__ = [
    "CriticalDependencyNode",
    "compute_criticality_score",
    "compute_pressure_mismatch_score",
    "enrich_pressure_score",
    "enrich_scores",
    "node_text_summary",
    "rank_criticality_first",
    "rank_flow_first",
]


def __getattr__(name):
    """Lazy exports keep `python -m trer.prisms.infrastructure.cdn` warning-free."""

    if name in __all__:
        from . import cdn

        return getattr(cdn, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
