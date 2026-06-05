# Market Simulations

This directory holds market-prism simulations for TRER. These experiments are
not trading advice; they are replay tools for separating market thesis from
execution mechanics.

## Execution Decoupling Prism

`execution_decoupling.py` models a low-premium SPY option trade across four
layers:

1. **Underlying reality** — SPY price / thesis state.
2. **Derivative quote** — option bid, ask, midpoint, spread.
3. **Broker execution** — stop trigger field and order type.
4. **Trader outcome** — realized P/L, no fill, false stop, or missed P/L.

The first fixture reproduces the important structure from Leslie's SPY put:

- entry ask: `0.23`
- position size: `2` contracts
- protective stop: `0.50`
- bid momentarily prints `0.49`
- ask remains wide at `0.80`
- spread-of-mid reaches `48.06%`
- thesis remains valid
- broker stop triggers on bid
- next frame bid recovers to `0.80`

The reconstructed event is classified as:

```text
BID_SPREAD_FALSE_STOP
```

because execution invalidated the position while the market thesis remained
valid and spread risk was elevated.

## Policy Comparison

The simulator now compares stop policies side-by-side:

- **Policy A:** option bid stop
- **Policy B:** option midpoint stop
- **Policy C:** underlying price invalidation
- **Policy D:** thesis-validity stop
- **Policy E:** hybrid bid stop + thesis invalidation confirmation

For the fixture path:

```text
Policy A exits at bid 0.49.
Policies B, C, D, and E survive.
```

The key metric is missed P/L after recovery:

```text
realized_pnl = (0.49 - 0.23) * 100 * 2 = $52
recovery_pnl = (0.80 - 0.23) * 100 * 2 = $114
missed_pnl  = $62
```

## Spread Risk

The current flag is:

```text
spread_risk = spread_pct_of_mid > 0.25
```

For low-premium SPY options, a 25–50% spread-of-mid can make bid-based stops
behave less like market-risk controls and more like spread-noise triggers.

## Run

From the repo root:

```bash
python3 -m trer.prisms.market.simulations.execution_decoupling
```

## Current Question

Was the stop triggered by changed market conditions, or by microstructure noise?

This simulation makes that question testable by replaying the same quote path
through different broker rules, such as `bid` trigger versus `mid` trigger,
`stop_market` versus `stop_limit`, or thesis-confirmed exits versus pure quote
stops.
