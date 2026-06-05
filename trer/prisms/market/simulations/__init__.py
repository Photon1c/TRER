"""Market simulation experiments for the TRER market prism."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .execution_decoupling import (
        BrokerStopRule,
        OptionQuoteFrame,
        Position,
        SimulationResult,
        StopTriggerEvent,
        simulate_stop_execution,
    )

_EXPORTS = {
    "BrokerStopRule",
    "OptionQuoteFrame",
    "Position",
    "SimulationResult",
    "StopTriggerEvent",
    "simulate_stop_execution",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        from . import execution_decoupling

        return getattr(execution_decoupling, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
