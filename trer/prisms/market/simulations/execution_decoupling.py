"""Execution-decoupling simulation for low-premium option stops.

This experiment separates four layers:

1. underlying reality: SPY path / thesis state
2. derivative quote: option bid/ask/mid
3. broker stop logic: which quote field triggers the stop
4. trader outcome: realized P/L versus avoided/false exit

It is a research scaffold, not trading advice.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

TriggerField = Literal["bid", "ask", "mid", "mark"]
OrderType = Literal["stop_market", "stop_limit"]
OptionType = Literal["call", "put"]
PolicyKind = Literal[
    "option_quote_stop",
    "underlying_price_invalidation",
    "thesis_validity_stop",
    "hybrid_quote_and_thesis_invalid",
]
UnderlyingDirection = Literal["above_or_equal", "below_or_equal"]

BID_SPREAD_FALSE_STOP = "BID_SPREAD_FALSE_STOP"
SPREAD_RISK_THRESHOLD = 0.25


@dataclass(frozen=True)
class Position:
    """A single option position being replayed through broker stop logic."""

    symbol: str
    option_type: OptionType
    entry_price: float
    quantity: int = 1
    multiplier: int = 100

    def pnl_at_price(self, price: float) -> float:
        """Return option P/L at a given executable option price."""

        return round((price - self.entry_price) * self.quantity * self.multiplier, 2)


@dataclass(frozen=True)
class BrokerStopRule:
    """A simplified broker stop model.

    `trigger_field` is the critical variable for this experiment. Many retail
    surprises happen when the trader's thesis is about SPY, but the stop is
    triggered by the option bid.
    """

    stop_price: float
    trigger_field: TriggerField = "bid"
    order_type: OrderType = "stop_market"
    limit_price: float | None = None


@dataclass(frozen=True)
class StopPolicy:
    """A named exit policy for side-by-side comparison."""

    name: str
    kind: PolicyKind
    stop_rule: BrokerStopRule | None = None
    underlying_stop_price: float | None = None
    underlying_direction: UnderlyingDirection = "above_or_equal"


@dataclass(frozen=True)
class OptionQuoteFrame:
    """One timestamped quote/state sample for an option contract."""

    timestamp: str
    underlying_price: float
    bid: float
    ask: float
    thesis_valid: bool
    label: str = ""
    mark: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def mid(self) -> float:
        return round((self.bid + self.ask) / 2, 4)

    @property
    def effective_mark(self) -> float:
        return self.mark if self.mark is not None else self.mid

    @property
    def spread(self) -> float:
        return round(self.ask - self.bid, 4)

    @property
    def spread_pct_of_mid(self) -> float:
        if self.mid == 0:
            return 0.0
        return round(self.spread / self.mid, 4)

    def trigger_value(self, field_name: TriggerField) -> float:
        if field_name == "bid":
            return self.bid
        if field_name == "ask":
            return self.ask
        if field_name == "mid":
            return self.mid
        return self.effective_mark


@dataclass(frozen=True)
class StopTriggerEvent:
    """A reconstructed stop event."""

    timestamp: str
    trigger_value: float
    fill_price: float | None
    false_stop: bool
    realized_pnl: float | None
    spread_pct_of_mid: float
    spread_risk: bool
    event_type: str
    quote: OptionQuoteFrame
    reason: str
    best_recovery_bid: float | None = None
    recovery_pnl: float | None = None
    missed_pnl: float | None = None


@dataclass(frozen=True)
class SimulationResult:
    """Outcome of replaying one position through one stop rule."""

    position: Position
    stop_rule: BrokerStopRule
    frames: tuple[OptionQuoteFrame, ...]
    stop_event: StopTriggerEvent | None
    max_spread: float
    max_spread_pct_of_mid: float
    spread_risk_threshold: float = SPREAD_RISK_THRESHOLD

    @property
    def stopped(self) -> bool:
        return self.stop_event is not None

    @property
    def false_stop(self) -> bool:
        return bool(self.stop_event and self.stop_event.false_stop)


@dataclass(frozen=True)
class PolicyOutcome:
    """Result of replaying one named stop policy."""

    policy: StopPolicy
    stopped: bool
    stop_event: StopTriggerEvent | None
    terminal_bid: float | None
    terminal_pnl: float | None

    @property
    def false_stop(self) -> bool:
        return bool(self.stop_event and self.stop_event.false_stop)


@dataclass(frozen=True)
class PolicyComparison:
    """Side-by-side outcomes for multiple stop policies."""

    position: Position
    frames: tuple[OptionQuoteFrame, ...]
    outcomes: tuple[PolicyOutcome, ...]
    spread_risk_threshold: float = SPREAD_RISK_THRESHOLD


def default_policy_suite(stop_price: float, underlying_stop_price: float | None = None) -> tuple[StopPolicy, ...]:
    """Return the baseline policies suggested by the first SPY put experiment."""

    return (
        StopPolicy(
            name="Policy A: option bid stop",
            kind="option_quote_stop",
            stop_rule=BrokerStopRule(stop_price=stop_price, trigger_field="bid", order_type="stop_market"),
        ),
        StopPolicy(
            name="Policy B: option mid stop",
            kind="option_quote_stop",
            stop_rule=BrokerStopRule(stop_price=stop_price, trigger_field="mid", order_type="stop_market"),
        ),
        StopPolicy(
            name="Policy C: underlying price invalidation",
            kind="underlying_price_invalidation",
            underlying_stop_price=underlying_stop_price,
            underlying_direction="above_or_equal",
        ),
        StopPolicy(name="Policy D: thesis-validity stop", kind="thesis_validity_stop"),
        StopPolicy(
            name="Policy E: bid stop AND thesis invalid",
            kind="hybrid_quote_and_thesis_invalid",
            stop_rule=BrokerStopRule(stop_price=stop_price, trigger_field="bid", order_type="stop_market"),
        ),
    )


def simulate_stop_execution(
    position: Position,
    stop_rule: BrokerStopRule,
    frames: list[OptionQuoteFrame] | tuple[OptionQuoteFrame, ...],
    *,
    spread_risk_threshold: float = SPREAD_RISK_THRESHOLD,
) -> SimulationResult:
    """Replay quote frames and return the first stop trigger, if any.

    A false stop is defined narrowly here: the broker stop triggers while the
    trade thesis remains valid. The simulator does not decide whether a thesis
    is correct; it accepts `thesis_valid` as scenario input so different thesis
    rules can be tested later.
    """

    ordered_frames = tuple(sorted(frames, key=lambda frame: frame.timestamp))
    stop_event: StopTriggerEvent | None = None

    for index, frame in enumerate(ordered_frames):
        trigger_value = frame.trigger_value(stop_rule.trigger_field)
        if trigger_value > stop_rule.stop_price:
            continue

        fill_price = _fill_price(frame, stop_rule)
        stop_event = _build_stop_event(
            position=position,
            stop_rule=stop_rule,
            frame=frame,
            trigger_value=trigger_value,
            fill_price=fill_price,
            future_frames=ordered_frames[index + 1 :],
            spread_risk_threshold=spread_risk_threshold,
        )
        break

    return SimulationResult(
        position=position,
        stop_rule=stop_rule,
        frames=ordered_frames,
        stop_event=stop_event,
        max_spread=max((frame.spread for frame in ordered_frames), default=0.0),
        max_spread_pct_of_mid=max((frame.spread_pct_of_mid for frame in ordered_frames), default=0.0),
        spread_risk_threshold=spread_risk_threshold,
    )


def compare_stop_policies(
    position: Position,
    frames: list[OptionQuoteFrame] | tuple[OptionQuoteFrame, ...],
    policies: list[StopPolicy] | tuple[StopPolicy, ...],
    *,
    spread_risk_threshold: float = SPREAD_RISK_THRESHOLD,
) -> PolicyComparison:
    """Replay the same quote path through multiple exit policies."""

    ordered_frames = tuple(sorted(frames, key=lambda frame: frame.timestamp))
    terminal_bid = ordered_frames[-1].bid if ordered_frames else None
    terminal_pnl = position.pnl_at_price(terminal_bid) if terminal_bid is not None else None

    outcomes: list[PolicyOutcome] = []
    for policy in policies:
        stop_event = _first_policy_stop_event(position, policy, ordered_frames, spread_risk_threshold)
        outcomes.append(
            PolicyOutcome(
                policy=policy,
                stopped=stop_event is not None,
                stop_event=stop_event,
                terminal_bid=terminal_bid,
                terminal_pnl=terminal_pnl,
            )
        )

    return PolicyComparison(
        position=position,
        frames=ordered_frames,
        outcomes=tuple(outcomes),
        spread_risk_threshold=spread_risk_threshold,
    )


def load_simulation_payload(path: str | Path) -> tuple[Position, BrokerStopRule, list[OptionQuoteFrame]]:
    """Load a simulation payload from JSON."""

    payload = json.loads(Path(path).read_text())
    position = Position(**payload["position"])
    stop_rule = BrokerStopRule(**payload["stop_rule"])
    frames = [OptionQuoteFrame(**frame) for frame in payload["frames"]]
    return position, stop_rule, frames


def result_to_dict(result: SimulationResult) -> dict[str, Any]:
    """Serialize a simulation result for reports or fixtures."""

    data = asdict(result)
    data["stopped"] = result.stopped
    data["false_stop"] = result.false_stop
    return data


def comparison_to_dict(comparison: PolicyComparison) -> dict[str, Any]:
    """Serialize a policy comparison for reports or fixtures."""

    data = asdict(comparison)
    data["outcomes"] = [
        {
            **asdict(outcome),
            "false_stop": outcome.false_stop,
        }
        for outcome in comparison.outcomes
    ]
    return data


def _first_policy_stop_event(
    position: Position,
    policy: StopPolicy,
    frames: tuple[OptionQuoteFrame, ...],
    spread_risk_threshold: float,
) -> StopTriggerEvent | None:
    for index, frame in enumerate(frames):
        if policy.kind == "option_quote_stop":
            if policy.stop_rule is None:
                raise ValueError(f"{policy.name} requires a stop_rule")
            trigger_value = frame.trigger_value(policy.stop_rule.trigger_field)
            if trigger_value > policy.stop_rule.stop_price:
                continue
            return _build_stop_event(
                position=position,
                stop_rule=policy.stop_rule,
                frame=frame,
                trigger_value=trigger_value,
                fill_price=_fill_price(frame, policy.stop_rule),
                future_frames=frames[index + 1 :],
                spread_risk_threshold=spread_risk_threshold,
            )

        if policy.kind == "underlying_price_invalidation":
            if policy.underlying_stop_price is None:
                continue
            if not _underlying_invalidated(frame, policy):
                continue
            stop_rule = BrokerStopRule(stop_price=frame.bid, trigger_field="bid", order_type="stop_market")
            return _build_stop_event(
                position=position,
                stop_rule=stop_rule,
                frame=frame,
                trigger_value=frame.underlying_price,
                fill_price=frame.bid,
                future_frames=frames[index + 1 :],
                spread_risk_threshold=spread_risk_threshold,
                false_stop=False,
                event_type="UNDERLYING_INVALIDATION_STOP",
                reason=f"underlying={frame.underlying_price:.2f} invalidated policy at {policy.underlying_stop_price:.2f}",
            )

        if policy.kind == "thesis_validity_stop":
            if frame.thesis_valid:
                continue
            stop_rule = BrokerStopRule(stop_price=frame.bid, trigger_field="bid", order_type="stop_market")
            return _build_stop_event(
                position=position,
                stop_rule=stop_rule,
                frame=frame,
                trigger_value=frame.bid,
                fill_price=frame.bid,
                future_frames=frames[index + 1 :],
                spread_risk_threshold=spread_risk_threshold,
                false_stop=False,
                event_type="THESIS_INVALIDATION_STOP",
                reason="thesis_valid=False",
            )

        if policy.kind == "hybrid_quote_and_thesis_invalid":
            if policy.stop_rule is None:
                raise ValueError(f"{policy.name} requires a stop_rule")
            trigger_value = frame.trigger_value(policy.stop_rule.trigger_field)
            if trigger_value > policy.stop_rule.stop_price or frame.thesis_valid:
                continue
            return _build_stop_event(
                position=position,
                stop_rule=policy.stop_rule,
                frame=frame,
                trigger_value=trigger_value,
                fill_price=_fill_price(frame, policy.stop_rule),
                future_frames=frames[index + 1 :],
                spread_risk_threshold=spread_risk_threshold,
                false_stop=False,
                event_type="HYBRID_CONFIRMED_STOP",
            )

    return None


def _build_stop_event(
    *,
    position: Position,
    stop_rule: BrokerStopRule,
    frame: OptionQuoteFrame,
    trigger_value: float,
    fill_price: float | None,
    future_frames: tuple[OptionQuoteFrame, ...],
    spread_risk_threshold: float,
    false_stop: bool | None = None,
    event_type: str | None = None,
    reason: str | None = None,
) -> StopTriggerEvent:
    realized_pnl = position.pnl_at_price(fill_price) if fill_price is not None else None
    spread_risk = frame.spread_pct_of_mid > spread_risk_threshold
    inferred_false_stop = frame.thesis_valid if false_stop is None else false_stop
    inferred_event_type = event_type or _event_type(stop_rule, inferred_false_stop, spread_risk)
    best_recovery_bid = _best_future_bid(future_frames)
    recovery_pnl = position.pnl_at_price(best_recovery_bid) if best_recovery_bid is not None else None
    missed_pnl = None
    if realized_pnl is not None and recovery_pnl is not None and recovery_pnl > realized_pnl:
        missed_pnl = round(recovery_pnl - realized_pnl, 2)

    return StopTriggerEvent(
        timestamp=frame.timestamp,
        trigger_value=trigger_value,
        fill_price=fill_price,
        false_stop=inferred_false_stop,
        realized_pnl=realized_pnl,
        spread_pct_of_mid=frame.spread_pct_of_mid,
        spread_risk=spread_risk,
        event_type=inferred_event_type,
        quote=frame,
        reason=reason
        or (
            f"{stop_rule.trigger_field}={trigger_value:.2f} <= stop={stop_rule.stop_price:.2f}; "
            f"thesis_valid={frame.thesis_valid}; spread_risk={spread_risk}"
        ),
        best_recovery_bid=best_recovery_bid,
        recovery_pnl=recovery_pnl,
        missed_pnl=missed_pnl,
    )


def _event_type(stop_rule: BrokerStopRule, false_stop: bool, spread_risk: bool) -> str:
    if false_stop and spread_risk and stop_rule.trigger_field == "bid":
        return BID_SPREAD_FALSE_STOP
    if false_stop:
        return "FALSE_STOP"
    if stop_rule.order_type == "stop_limit":
        return "STOP_LIMIT_TRIGGER"
    return "STOP_TRIGGER"


def _best_future_bid(frames: tuple[OptionQuoteFrame, ...]) -> float | None:
    if not frames:
        return None
    return max(frame.bid for frame in frames)


def _underlying_invalidated(frame: OptionQuoteFrame, policy: StopPolicy) -> bool:
    if policy.underlying_stop_price is None:
        return False
    if policy.underlying_direction == "above_or_equal":
        return frame.underlying_price >= policy.underlying_stop_price
    return frame.underlying_price <= policy.underlying_stop_price


def _fill_price(frame: OptionQuoteFrame, stop_rule: BrokerStopRule) -> float | None:
    if stop_rule.order_type == "stop_market":
        return frame.bid

    limit_price = stop_rule.limit_price if stop_rule.limit_price is not None else stop_rule.stop_price
    if frame.bid >= limit_price:
        return frame.bid
    return None


def _demo_payload_path() -> Path:
    return Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "market" / "spy_put_execution_decoupling.json"


def main() -> None:
    position, stop_rule, frames = load_simulation_payload(_demo_payload_path())
    result = simulate_stop_execution(position, stop_rule, frames)
    comparison = compare_stop_policies(
        position,
        frames,
        default_policy_suite(stop_rule.stop_price, underlying_stop_price=752.00),
    )
    print(
        json.dumps(
            {
                "single_policy_result": result_to_dict(result),
                "policy_comparison": comparison_to_dict(comparison),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
