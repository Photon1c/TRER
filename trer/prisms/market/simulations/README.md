# Market Simulations

This directory holds market-prism simulations for TRER. These experiments are
not trading advice; they are replay tools for separating market thesis from
execution mechanics.

## Execution Decoupling

`execution_decoupling.py` models a low-premium SPY option trade across four
layers:

1. **Underlying reality** — SPY price / thesis state.
2. **Derivative quote** — option bid, ask, midpoint, spread.
3. **Broker execution** — stop trigger field and order type.
4. **Trader outcome** — realized P/L, no fill, or false stop.

The first fixture reproduces the important structure from Leslie's SPY put:

- entry ask: `0.23`
- protective stop: `0.50`
- bid momentarily prints `0.49`
- ask remains wide at `0.80`
- thesis remains valid
- broker stop triggers on bid

The reconstructed event is classified as a **false stop** because execution
invalidated the position while the market thesis remained valid.

## Run

From the repo root:

```bash
python3 -m trer.prisms.market.simulations.execution_decoupling
```

## Current Question

Was the stop triggered by changed market conditions, or by microstructure noise?

This simulation makes that question testable by replaying the same quote path
through different broker rules, such as `bid` trigger versus `mid` trigger or
`stop_market` versus `stop_limit`.
