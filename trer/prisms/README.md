# TRER Prisms

Prisms are domain adapters and interpretation layers around the TRER core.
They should translate domain-specific observations into core nodes/events/edges,
or translate reconstructed timelines back into domain language.

They should **not** become load-bearing dependencies of the core engine.

## Initial Prism Map

- `perception/` — Falcon Vision-style detections and visual observations.
- `workflow/` — Pixel Office-style coordination, task flow, and queue state.
- `market/` — Gamma Reflexivity-style price/news/options pressure timelines, including execution-decoupling simulations.
- `inventory/` — Starbucks-style reconciliation, queue growth, and ambiguity routing.
- `criminology/` — burglary-ring timelines, temporal linking, uncertainty scoring.
- `infrastructure/` — Critical Dependency Observatory-style maintenance, inspection, ownership, and failure events.
- `narrative/` — human-readable explanations and investigation summaries.

## Boundary Rule

If a feature needs a domain noun to make sense, it probably belongs in a prism.
If it only needs nodes, edges, events, timelines, evidence, and uncertainty, it
may belong in core.
