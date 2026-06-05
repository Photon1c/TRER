"""Market simulation experiments for the TRER market prism."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .execution_decoupling import (
        BID_SPREAD_FALSE_STOP,
        SPREAD_RISK_THRESHOLD,
        BrokerStopRule,
        OptionQuoteFrame,
        PolicyComparison,
        PolicyOutcome,
        Position,
        SimulationResult,
        StopPolicy,
        StopTriggerEvent,
        compare_stop_policies,
        default_policy_suite,
        simulate_stop_execution,
    )

_EXPORTS = {
    "BID_SPREAD_FALSE_STOP",
    "SPREAD_RISK_THRESHOLD",
    "BrokerStopRule",
    "OptionQuoteFrame",
    "PolicyComparison",
    "PolicyOutcome",
    "Position",
    "SimulationResult",
    "StopPolicy",
    "StopTriggerEvent",
    "compare_stop_policies",
    "default_policy_suite",
    "simulate_stop_execution",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        from . import execution_decoupling

        return getattr(execution_decoupling, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
