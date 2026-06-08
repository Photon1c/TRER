"""Private repo-pressure prism for OpenClaw/TRER ecosystem triage."""

__all__ = [
    "RepoPressureNode",
    "compute_repo_scores",
    "rank_repos",
    "recommended_action",
]


def __getattr__(name):
    if name in __all__:
        from . import dashboard

        return getattr(dashboard, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
