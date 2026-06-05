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


@dataclass(frozen=True)
class Position:
    """A single option position being replayed through broker stop logic."""

    symbol: str
    option_type: OptionType
    entry_price: float
    quantity: int = 1
    multiplier: int = 100


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
    quote: OptionQuoteFrame
    reason: str


@dataclass(frozen=True)
class SimulationResult:
    """Outcome of replaying one position through one stop rule."""

    position: Position
    stop_rule: BrokerStopRule
    frames: tuple[OptionQuoteFrame, ...]
    stop_event: StopTriggerEvent | None
    max_spread: float
    max_spread_pct_of_mid: float

    @property
    def stopped(self) -> bool:
        return self.stop_event is not None

    @property
    def false_stop(self) -> bool:
        return bool(self.stop_event and self.stop_event.false_stop)


def simulate_stop_execution(
    position: Position,
    stop_rule: BrokerStopRule,
    frames: list[OptionQuoteFrame] | tuple[OptionQuoteFrame, ...],
) -> SimulationResult:
    """Replay quote frames and return the first stop trigger, if any.

    A false stop is defined narrowly here: the broker stop triggers while the
    trade thesis remains valid. The simulator does not decide whether a thesis
    is correct; it accepts `thesis_valid` as scenario input so different thesis
    rules can be tested later.
    """

    ordered_frames = tuple(sorted(frames, key=lambda frame: frame.timestamp))
    stop_event: StopTriggerEvent | None = None

    for frame in ordered_frames:
        trigger_value = frame.trigger_value(stop_rule.trigger_field)
        if trigger_value > stop_rule.stop_price:
            continue

        fill_price = _fill_price(frame, stop_rule)
        realized_pnl = None
        if fill_price is not None:
            realized_pnl = round((fill_price - position.entry_price) * position.quantity * position.multiplier, 2)

        stop_event = StopTriggerEvent(
            timestamp=frame.timestamp,
            trigger_value=trigger_value,
            fill_price=fill_price,
            false_stop=frame.thesis_valid,
            realized_pnl=realized_pnl,
            spread_pct_of_mid=frame.spread_pct_of_mid,
            quote=frame,
            reason=(
                f"{stop_rule.trigger_field}={trigger_value:.2f} <= stop={stop_rule.stop_price:.2f}; "
                f"thesis_valid={frame.thesis_valid}"
            ),
        )
        break

    return SimulationResult(
        position=position,
        stop_rule=stop_rule,
        frames=ordered_frames,
        stop_event=stop_event,
        max_spread=max((frame.spread for frame in ordered_frames), default=0.0),
        max_spread_pct_of_mid=max((frame.spread_pct_of_mid for frame in ordered_frames), default=0.0),
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
    print(json.dumps(result_to_dict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
